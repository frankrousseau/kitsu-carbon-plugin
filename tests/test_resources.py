"""
Tests for carbon plugin API resources.

Requirements:
    - zou must be installed with test dependencies: pip install zou[test]
    - Plugin must be installed: pip install -e .

Run:
    pytest tests/ -v
"""
from zou.utils.test_helpers import ApiDBTestCase

from sqlalchemy.orm.attributes import flag_modified

from zou.app.models.person import Person
from zou.app.services import tasks_service

from carbon.models import CarbonFactor


class CarbonResourcesTestCase(ApiDBTestCase):

    def setUp(self):
        super().setUp()

        # Create project hierarchy
        self.generate_fixture_project_status()
        self.generate_fixture_project()
        self.generate_fixture_asset_type()
        self.generate_fixture_department()
        self.generate_fixture_task_type()
        self.generate_fixture_task_status()
        self.generate_fixture_person()
        self.generate_fixture_assigner()

        # Create sequences and shots
        self.generate_fixture_sequence()
        self.generate_fixture_shot()

        # Create asset
        self.generate_fixture_asset()

        # Create tasks
        self.generate_fixture_task()
        self.generate_fixture_shot_task()

        # Set up carbon factors
        self._create_carbon_factors()

        # Set person country
        self._set_person_country(self.person.id, "FR")

    def _create_carbon_factors(self):
        factors_data = [
            ("FR", "France", 12.0, 10.0),
            ("US", "United States", 95.0, 58.0),
        ]
        for code, name, rendering, workbench in factors_data:
            CarbonFactor.create_no_commit(
                country_code=code,
                country_name=name,
                rendering_co2e=rendering,
                workbench_co2e=workbench,
            )
        CarbonFactor.commit()

    def _set_person_country(self, person_id, country_code):
        person = Person.get(person_id)
        if person:
            if person.data is None:
                person.data = {}
            person.data["country"] = country_code
            flag_modified(person, "data")
            Person.commit()


class CarbonFactorsResourceTestCase(CarbonResourcesTestCase):

    def test_get_factors(self):
        response = self.get("/plugins/carbon/factors")

        self.assertEqual(len(response), 2)
        codes = [f["country_code"] for f in response]
        self.assertIn("FR", codes)
        self.assertIn("US", codes)

    def test_get_factor_by_code(self):
        response = self.get("/plugins/carbon/factors/FR")

        self.assertEqual(response["country_code"], "FR")
        self.assertEqual(response["country_name"], "France")
        self.assertEqual(response["rendering_co2e"], 12.0)
        self.assertEqual(response["workbench_co2e"], 10.0)

    def test_get_factor_case_insensitive(self):
        response = self.get("/plugins/carbon/factors/fr")

        self.assertEqual(response["country_code"], "FR")

    def test_get_factor_not_found(self):
        self.get("/plugins/carbon/factors/XX", code=404)

    def test_create_factor(self):
        data = {
            "country_code": "JP",
            "country_name": "Japan",
            "rendering_co2e": 120.0,
            "workbench_co2e": 70.0,
        }

        response = self.post("/plugins/carbon/factors", data)

        self.assertEqual(response["country_code"], "JP")
        self.assertEqual(response["country_name"], "Japan")
        factor = CarbonFactor.get_by(country_code="JP")
        self.assertIsNotNone(factor)

    def test_update_factor(self):
        data = {
            "country_code": "FR",
            "country_name": "France (updated)",
            "rendering_co2e": 15.0,
            "workbench_co2e": 12.0,
        }

        response = self.post("/plugins/carbon/factors", data)

        self.assertEqual(response["country_name"], "France (updated)")
        self.assertEqual(response["workbench_co2e"], 12.0)

    def test_create_factor_invalid_code(self):
        data = {
            "country_code": "INVALID",
            "country_name": "Test",
            "rendering_co2e": 10.0,
            "workbench_co2e": 10.0,
        }

        self.post("/plugins/carbon/factors", data, code=400)

    def test_create_factor_missing_name(self):
        data = {
            "country_code": "XX",
            "country_name": "",
            "rendering_co2e": 10.0,
            "workbench_co2e": 10.0,
        }

        self.post("/plugins/carbon/factors", data, code=400)


class SequenceFootprintResourceTestCase(CarbonResourcesTestCase):

    def test_get_sequence_footprint(self):
        tasks_service.create_or_update_time_spent(
            self.shot_task.id,
            self.person.id,
            "2024-01-15",
            120,
        )

        response = self.get(
            f"/plugins/carbon/productions/{self.project_id}"
            "/footprint/sequences"
        )

        self.assertEqual(response["project_id"], str(self.project_id))
        self.assertIn("details", response)
        self.assertIn("by_sequence", response)
        self.assertIn("by_task_type", response)
        self.assertIn("total_co2_kg", response)
        self.assertIn("total_man_days", response)

    def test_get_sequence_footprint_empty(self):
        response = self.get(
            f"/plugins/carbon/productions/{self.project_id}"
            "/footprint/sequences"
        )

        self.assertEqual(response["details"], [])
        self.assertEqual(response["total_co2_kg"], 0.0)


class AssetFootprintResourceTestCase(CarbonResourcesTestCase):

    def test_get_asset_footprint(self):
        tasks_service.create_or_update_time_spent(
            self.task.id,
            self.person.id,
            "2024-01-15",
            180,
        )

        response = self.get(
            f"/plugins/carbon/productions/{self.project_id}"
            "/footprint/assets"
        )

        self.assertEqual(response["project_id"], str(self.project_id))
        self.assertIn("details", response)
        self.assertIn("by_asset_type", response)
        self.assertGreater(response["total_co2_kg"], 0)


class SummaryFootprintResourceTestCase(CarbonResourcesTestCase):

    def test_get_summary(self):
        tasks_service.create_or_update_time_spent(
            self.task.id,
            self.person.id,
            "2024-01-15",
            240,
        )

        response = self.get(
            f"/plugins/carbon/productions/{self.project_id}"
            "/footprint/summary"
        )

        self.assertEqual(response["project_id"], str(self.project_id))
        self.assertIn("total_co2_kg", response)
        self.assertIn("total_man_days", response)
        self.assertIn("weekly_average_co2_kg", response)
        self.assertIn("num_weeks_with_data", response)
        # 240 min = 4h * 10g/h = 40g = 0.04kg
        self.assertAlmostEqual(response["total_co2_kg"], 0.04, places=2)
        # 240 min / 60 / 8 = 0.5 man days
        self.assertAlmostEqual(response["total_man_days"], 0.5, places=2)

    def test_get_summary_empty(self):
        response = self.get(
            f"/plugins/carbon/productions/{self.project_id}"
            "/footprint/summary"
        )

        self.assertEqual(response["total_co2_kg"], 0.0)
        self.assertEqual(response["total_duration_minutes"], 0)


class EpisodeFootprintResourceTestCase(CarbonResourcesTestCase):

    def test_get_episode_footprint(self):
        response = self.get(
            f"/plugins/carbon/productions/{self.project_id}"
            "/footprint/episodes"
        )

        self.assertEqual(response["project_id"], str(self.project_id))
        self.assertIn("details", response)
        self.assertIn("by_episode", response)


class AccessControlTestCase(CarbonResourcesTestCase):

    def test_unauthenticated_access_denied(self):
        self.log_out()
        self.get("/plugins/carbon/factors", code=401)

    def test_non_admin_cannot_create_factor(self):
        self.generate_fixture_user_cg_artist()
        self.log_in_cg_artist()

        data = {
            "country_code": "JP",
            "country_name": "Japan",
            "rendering_co2e": 120.0,
            "workbench_co2e": 70.0,
        }

        self.post("/plugins/carbon/factors", data, code=403)
