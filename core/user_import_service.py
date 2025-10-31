import csv
import io
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from core.models import UserRole, Role
from location.models import Location, UserDistrict  # openIMIS standard

User = get_user_model()


class UserImportService:
    """
    Service d'importation d'utilisateurs à partir d'un fichier CSV.
    Gère les rôles, localités, téléphone, mot de passe et langue.
    """

    REQUIRED_FIELDS = ["username", "email", "first_name", "last_name"]

    @classmethod
    def import_users(cls, file, delimiter=",", dry_run=False):
        """
        Importe les utilisateurs à partir d'un CSV.
        Colonnes supportées :
          username,email,first_name,last_name,password,phone_number,language,roles,regions,districts
        """
        report = {"created": 0, "updated": 0, "errors": []}

        decoded_file = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded_file), delimiter=delimiter)

        try:
            with transaction.atomic():
                for line_no, row in enumerate(reader, start=2):
                    try:
                        # Vérifie les champs obligatoires
                        missing = [f for f in cls.REQUIRED_FIELDS if not row.get(f)]
                        if missing:
                            raise ValidationError(f"Colonnes manquantes: {', '.join(missing)}")

                        username = row["username"].strip()
                        email = row["email"].strip()
                        first_name = row["first_name"].strip()
                        last_name = row["last_name"].strip()

                        user_defaults = {
                            "email": email,
                            "first_name": first_name,
                            "last_name": last_name,
                            "is_active": True,
                        }

                        # Téléphone
                        if row.get("phone_number"):
                            user_defaults["phone"] = row["phone_number"].strip()

                        # Langue préférée
                        if row.get("language"):
                            user_defaults["language"] = row["language"].strip().lower()

                        # Création / mise à jour
                        user, created = User.objects.get_or_create(username=username, defaults=user_defaults)

                        if not created:
                            for k, v in user_defaults.items():
                                setattr(user, k, v)
                            user.save()
                            report["updated"] += 1
                        else:
                            report["created"] += 1

                        # Mot de passe
                        if row.get("password"):
                            user.set_password(row["password"].strip())
                            user.save()

                        # Rôles
                        if row.get("roles"):
                            role_names = [r.strip() for r in row["roles"].split(";") if r.strip()]
                            for role_name in role_names:
                                role = Role.objects.filter(code__iexact=role_name).first()
                                if role:
                                    UserRole.objects.get_or_create(user=user, role=role)

                        # Nettoyage des localités existantes
                        UserDistrict.objects.filter(user=user).delete()

                        # Régions
                        if row.get("regions"):
                            regions = [r.strip() for r in row["regions"].split(";") if r.strip()]
                            for r_name in regions:
                                loc = Location.objects.filter(name__iexact=r_name, type="R").first()
                                if loc:
                                    UserDistrict.objects.get_or_create(user=user, location=loc)

                        # Districts
                        if row.get("districts"):
                            districts = [d.strip() for d in row["districts"].split(";") if d.strip()]
                            for d_name in districts:
                                loc = Location.objects.filter(name__iexact=d_name, type="D").first()
                                if loc:
                                    UserDistrict.objects.get_or_create(user=user, location=loc)

                    except Exception as e:
                        report["errors"].append(f"Ligne {line_no}: {e}")

                if dry_run:
                    transaction.set_rollback(True)

        except Exception as e:
            report["errors"].append(str(e))

        return report
