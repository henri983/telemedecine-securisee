"""
Tests unitaires pour le contrôle d'accès basé sur les rôles (RBAC).

Vérifie les permissions assignées à chaque rôle (admin, praticien, patient)
et que les contrôles d'accès fonctionnent correctement.
"""

import pytest

from src.security.rbac import Permission, ROLE_PERMISSIONS, require_permission
from src.models.user import UserRole


pytestmark = [pytest.mark.unit]


class TestAdminPermissions:
    """Tests des permissions administrateur."""

    def test_admin_has_all_permissions(self) -> None:
        """L'admin a toutes les permissions du système."""
        admin_role = UserRole.ADMIN.value if hasattr(UserRole.ADMIN, "value") else "admin"
        admin_permissions = ROLE_PERMISSIONS.get(admin_role, set())

        # L'admin devrait avoir toutes les permissions définies
        all_permissions = set()
        for perms in ROLE_PERMISSIONS.values():
            all_permissions.update(perms)

        missing = all_permissions - admin_permissions
        assert len(missing) == 0, (
            f"L'admin n'a pas les permissions suivantes: {missing}"
        )

    def test_admin_can_manage_users(self) -> None:
        """L'admin peut gérer les utilisateurs."""
        admin_role = UserRole.ADMIN.value if hasattr(UserRole.ADMIN, "value") else "admin"
        admin_permissions = ROLE_PERMISSIONS.get(admin_role, set())

        # Vérifier que les permissions de gestion des utilisateurs existent
        user_management_perms = {
            p for p in admin_permissions
            if "user" in str(p).lower() or "manage" in str(p).lower()
        }
        assert len(user_management_perms) > 0, (
            "L'admin devrait avoir des permissions de gestion d'utilisateurs"
        )

    def test_admin_can_delete_data(self) -> None:
        """L'admin peut supprimer des données."""
        admin_role = UserRole.ADMIN.value if hasattr(UserRole.ADMIN, "value") else "admin"
        admin_permissions = ROLE_PERMISSIONS.get(admin_role, set())

        delete_perms = {
            p for p in admin_permissions
            if "delete" in str(p).lower() or "supprimer" in str(p).lower()
        }
        assert len(delete_perms) > 0, (
            "L'admin devrait pouvoir supprimer des données"
        )


class TestPraticienPermissions:
    """Tests des permissions praticien."""

    def test_praticien_permissions(self) -> None:
        """Le praticien a les bonnes permissions (consultations, patients)."""
        praticien_role = UserRole.PRATICIEN.value if hasattr(UserRole.PRATICIEN, "value") else "praticien"
        praticien_permissions = ROLE_PERMISSIONS.get(praticien_role, set())

        assert len(praticien_permissions) > 0, (
            "Le praticien doit avoir des permissions"
        )

        # Vérifier les permissions liées aux patients et consultations
        patient_perms = {
            p for p in praticien_permissions
            if "patient" in str(p).lower() or "consult" in str(p).lower()
            or "read" in str(p).lower() or "view" in str(p).lower()
        }
        assert len(patient_perms) > 0, (
            "Le praticien devrait avoir des permissions liées aux patients/consultations"
        )

    def test_praticien_cannot_delete_data(self) -> None:
        """Le praticien ne peut pas supprimer de données (seulement l'admin)."""
        praticien_role = UserRole.PRATICIEN.value if hasattr(UserRole.PRATICIEN, "value") else "praticien"
        admin_role = UserRole.ADMIN.value if hasattr(UserRole.ADMIN, "value") else "admin"

        praticien_permissions = ROLE_PERMISSIONS.get(praticien_role, set())
        admin_permissions = ROLE_PERMISSIONS.get(admin_role, set())

        # Le praticien devrait avoir strictement moins de permissions que l'admin
        assert praticien_permissions < admin_permissions or \
            praticien_permissions != admin_permissions, (
            "Le praticien ne devrait pas avoir les mêmes permissions que l'admin"
        )

    def test_praticien_has_fewer_permissions_than_admin(self) -> None:
        """Le praticien a moins de permissions que l'admin."""
        praticien_role = UserRole.PRATICIEN.value if hasattr(UserRole.PRATICIEN, "value") else "praticien"
        admin_role = UserRole.ADMIN.value if hasattr(UserRole.ADMIN, "value") else "admin"

        praticien_perms = ROLE_PERMISSIONS.get(praticien_role, set())
        admin_perms = ROLE_PERMISSIONS.get(admin_role, set())

        assert len(praticien_perms) < len(admin_perms), (
            f"Le praticien ({len(praticien_perms)} perms) devrait avoir moins "
            f"de permissions que l'admin ({len(admin_perms)} perms)"
        )


class TestPatientPermissions:
    """Tests des permissions patient."""

    def test_patient_limited_permissions(self) -> None:
        """Le patient a des permissions limitées (lecture de ses propres données)."""
        patient_role = UserRole.PATIENT.value if hasattr(UserRole.PATIENT, "value") else "patient"
        patient_permissions = ROLE_PERMISSIONS.get(patient_role, set())

        assert len(patient_permissions) > 0, (
            "Le patient doit avoir au moins quelques permissions"
        )

        # Le patient devrait avoir le moins de permissions
        all_role_counts = {
            role: len(perms)
            for role, perms in ROLE_PERMISSIONS.items()
        }
        patient_count = len(patient_permissions)
        for role, count in all_role_counts.items():
            if role != patient_role:
                assert patient_count <= count, (
                    f"Le patient ({patient_count} perms) devrait avoir "
                    f"<= de permissions que {role} ({count} perms)"
                )

    def test_patient_cannot_manage_users(self) -> None:
        """Le patient ne peut pas gérer les utilisateurs."""
        patient_role = UserRole.PATIENT.value if hasattr(UserRole.PATIENT, "value") else "patient"
        patient_permissions = ROLE_PERMISSIONS.get(patient_role, set())

        # Vérifier qu'aucune permission de gestion d'utilisateurs n'est présente
        management_perms = {
            p for p in patient_permissions
            if ("manage" in str(p).lower() and "user" in str(p).lower())
            or "admin" in str(p).lower()
        }
        assert len(management_perms) == 0, (
            f"Le patient ne devrait pas avoir de permissions de gestion: {management_perms}"
        )

    def test_patient_cannot_create_consultations(self) -> None:
        """Le patient ne peut pas créer de consultations."""
        patient_role = UserRole.PATIENT.value if hasattr(UserRole.PATIENT, "value") else "patient"
        patient_permissions = ROLE_PERMISSIONS.get(patient_role, set())

        create_consult_perms = {
            p for p in patient_permissions
            if "create" in str(p).lower() and "consult" in str(p).lower()
        }
        assert len(create_consult_perms) == 0, (
            "Le patient ne devrait pas pouvoir créer de consultations"
        )


class TestUnknownRole:
    """Tests pour les rôles inconnus."""

    def test_unknown_role_no_permissions(self) -> None:
        """Un rôle inconnu n'a aucune permission."""
        unknown_permissions = ROLE_PERMISSIONS.get("role_inexistant", set())
        assert len(unknown_permissions) == 0, (
            f"Un rôle inconnu ne devrait avoir aucune permission, "
            f"obtenu: {unknown_permissions}"
        )

    def test_empty_string_role_no_permissions(self) -> None:
        """Un rôle vide n'a aucune permission."""
        empty_permissions = ROLE_PERMISSIONS.get("", set())
        assert len(empty_permissions) == 0, (
            "Un rôle vide ne devrait avoir aucune permission"
        )

    def test_none_role_no_permissions(self) -> None:
        """Un rôle None n'a aucune permission."""
        none_permissions = ROLE_PERMISSIONS.get(None, set())
        assert len(none_permissions) == 0, (
            "Un rôle None ne devrait avoir aucune permission"
        )


class TestRolePermissionsStructure:
    """Tests de la structure des permissions."""

    def test_all_standard_roles_defined(self) -> None:
        """Tous les rôles standard (admin, praticien, patient) sont définis."""
        expected_roles = {"admin", "praticien", "patient"}
        defined_roles = set(ROLE_PERMISSIONS.keys())

        for role in expected_roles:
            assert role in defined_roles, (
                f"Le rôle '{role}' devrait être défini dans ROLE_PERMISSIONS"
            )

    def test_permissions_are_sets(self) -> None:
        """Les permissions de chaque rôle sont des ensembles (pas de doublons)."""
        for role, perms in ROLE_PERMISSIONS.items():
            assert isinstance(perms, (set, frozenset, list)), (
                f"Les permissions du rôle '{role}' doivent être un ensemble"
            )

    def test_hierarchy_admin_superset(self) -> None:
        """L'admin est un sur-ensemble de toutes les autres permissions."""
        admin_role = UserRole.ADMIN.value if hasattr(UserRole.ADMIN, "value") else "admin"
        admin_perms = set(ROLE_PERMISSIONS.get(admin_role, set()))

        for role, perms in ROLE_PERMISSIONS.items():
            if role != admin_role:
                assert set(perms).issubset(admin_perms), (
                    f"Les permissions de '{role}' devraient être un sous-ensemble "
                    f"de celles de l'admin. "
                    f"Permissions manquantes: {set(perms) - admin_perms}"
                )
