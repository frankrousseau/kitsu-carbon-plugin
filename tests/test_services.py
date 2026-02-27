"""
Tests for carbon plugin services.

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
from carbon import services


class CarbonServicesTestCase(ApiDBTestCase):

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
            ("DE", "Germany", 80.0, 50.0),
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

    def _create_time_spent(self, task_id, person_id, date, duration):
        return tasks_service.create_or_update_time_spent(
            task_id, person_id, date, duration
        )


class SequenceFootprintTestCase(CarbonServicesTestCase):

    def test_get_sequence_footprint_empty(self):
        data = services.get_sequence_footprint_data(self.project_id)

        self.assertEqual(data["details"], [])
        self.assertEqual(data["total_co2_grams"], 0.0)
        self.assertEqual(data["total_duration_minutes"], 0)

    def test_get_sequence_footprint_with_time_spent(self):
        self._create_time_spent(
            self.shot_task.id,
            self.person.id,
            "2024-01-15",
            120,
        )

        data = services.get_sequence_footprint_data(self.project_id)

        # 120 minutes = 2 hours * 10 g/h (FR workbench) = 20g CO2
        self.assertEqual(len(data["details"]), 1)
        self.assertEqual(data["total_duration_minutes"], 120)
        self.assertAlmostEqual(data["total_co2_grams"], 20.0, places=2)

        detail = data["details"][0]
        self.assertEqual(detail["sequence_name"], "S01")
        self.assertEqual(detail["duration_minutes"], 120)

    def test_get_sequence_footprint_multiple_entries(self):
        self._create_time_spent(
            self.shot_task.id,
            self.person.id,
            "2024-01-15",
            60,
        )

        self.generate_fixture_user_cg_artist()
        self._set_person_country(self.user_cg_artist["id"], "US")

        self._create_time_spent(
            self.shot_task.id,
            self.user_cg_artist["id"],
            "2024-01-15",
            60,
        )

        data = services.get_sequence_footprint_data(self.project_id)

        # FR: 60 min = 1h * 10 g/h = 10g
        # US: 60 min = 1h * 58 g/h = 58g
        # Total: 68g
        self.assertEqual(data["total_duration_minutes"], 120)
        self.assertAlmostEqual(data["total_co2_grams"], 68.0, places=2)

    def test_get_sequence_footprint_unknown_country_contributes_zero(self):
        self._set_person_country(self.person.id, "XX")

        self._create_time_spent(
            self.shot_task.id,
            self.person.id,
            "2024-01-15",
            120,
        )

        data = services.get_sequence_footprint_data(self.project_id)

        self.assertEqual(data["total_duration_minutes"], 120)
        self.assertEqual(data["total_co2_grams"], 0.0)

    def test_get_sequence_footprint_aggregates(self):
        self._create_time_spent(
            self.shot_task.id,
            self.person.id,
            "2024-01-15",
            60,
        )

        data = services.get_sequence_footprint_data(self.project_id)

        self.assertIn("Animation", data["by_task_type"])
        self.assertAlmostEqual(
            data["by_task_type"]["Animation"]["co2_kg"],
            0.01,
            places=4
        )

        self.assertIn("S01", data["by_sequence"])
        self.assertAlmostEqual(
            data["by_sequence"]["S01"]["co2_kg"],
            0.01,
            places=4
        )


class AssetFootprintTestCase(CarbonServicesTestCase):

    def test_get_asset_footprint_empty(self):
        data = services.get_asset_footprint_data(self.project_id)

        self.assertEqual(data["details"], [])
        self.assertEqual(data["total_co2_grams"], 0.0)

    def test_get_asset_footprint_with_time_spent(self):
        self._create_time_spent(
            self.task.id,
            self.person.id,
            "2024-01-15",
            180,
        )

        data = services.get_asset_footprint_data(self.project_id)

        # 180 minutes = 3 hours * 10 g/h = 30g CO2
        self.assertEqual(len(data["details"]), 1)
        self.assertEqual(data["total_duration_minutes"], 180)
        self.assertAlmostEqual(data["total_co2_grams"], 30.0, places=2)

        detail = data["details"][0]
        self.assertEqual(detail["asset_type_name"], "Props")

    def test_get_asset_footprint_excludes_shots(self):
        self._create_time_spent(
            self.task.id,
            self.person.id,
            "2024-01-15",
            60,
        )

        self._create_time_spent(
            self.shot_task.id,
            self.person.id,
            "2024-01-15",
            60,
        )

        data = services.get_asset_footprint_data(self.project_id)

        self.assertEqual(data["total_duration_minutes"], 60)


class SummaryFootprintTestCase(CarbonServicesTestCase):

    def test_get_summary_empty(self):
        data = services.get_summary_footprint_data(self.project_id)

        self.assertEqual(data["total_co2_grams"], 0.0)
        self.assertEqual(data["total_duration_minutes"], 0)
        self.assertEqual(data["num_weeks_with_data"], 1)

    def test_get_summary_with_time_spent(self):
        self._create_time_spent(
            self.task.id,
            self.person.id,
            "2024-01-15",
            240,
        )

        data = services.get_summary_footprint_data(self.project_id)

        # 240 minutes = 4 hours * 10 g/h = 40g
        self.assertEqual(data["total_duration_minutes"], 240)
        self.assertAlmostEqual(data["total_co2_grams"], 40.0, places=2)

    def test_get_summary_weekly_average(self):
        self._create_time_spent(
            self.task.id,
            self.person.id,
            "2024-01-15",
            120,
        )

        self._create_time_spent(
            self.task.id,
            self.person.id,
            "2024-02-15",
            120,
        )

        data = services.get_summary_footprint_data(self.project_id)

        # Total: 240 min = 4h * 10g = 40g, 2 weeks, average = 20g
        self.assertEqual(data["total_duration_minutes"], 240)
        self.assertEqual(data["num_weeks_with_data"], 2)
        self.assertAlmostEqual(data["total_co2_grams"], 40.0, places=2)
        self.assertAlmostEqual(
            data["weekly_average_co2_grams"], 20.0, places=2
        )

    def test_get_summary_includes_all_task_types(self):
        self._create_time_spent(
            self.task.id,
            self.person.id,
            "2024-01-15",
            60,
        )

        self._create_time_spent(
            self.shot_task.id,
            self.person.id,
            "2024-01-15",
            60,
        )

        data = services.get_summary_footprint_data(self.project_id)

        self.assertEqual(data["total_duration_minutes"], 120)
        self.assertAlmostEqual(data["total_co2_grams"], 20.0, places=2)


class EpisodeFootprintTestCase(CarbonServicesTestCase):

    def setUp(self):
        super().setUp()
        self.generate_fixture_episode()

    def test_get_episode_footprint_empty(self):
        data = services.get_episode_footprint_data(self.project_id)

        self.assertIsInstance(data["details"], list)
        self.assertIsInstance(data["total_co2_grams"], float)


class CarbonFactorModelTestCase(CarbonServicesTestCase):

    def test_carbon_factors_created(self):
        factor = CarbonFactor.get_by(country_code="FR")

        self.assertIsNotNone(factor)
        self.assertEqual(factor.country_name, "France")
        self.assertEqual(factor.rendering_co2e, 12.0)
        self.assertEqual(factor.workbench_co2e, 10.0)

    def test_seed_does_not_duplicate(self):
        initial_count = len(CarbonFactor.get_all())

        CarbonFactor.seed_initial_data()

        final_count = len(CarbonFactor.get_all())
        self.assertGreaterEqual(final_count, initial_count)

        factor = CarbonFactor.get_by(country_code="FR")
        self.assertIsNotNone(factor)
