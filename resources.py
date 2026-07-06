from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required

from zou.app.mixin import ArgsMixin
from zou.app.services import projects_service, user_service
from zou.app.utils import permissions

from .models import CarbonFactor
from . import services


class CarbonFactorsResource(MethodView):

    @jwt_required()
    def get(self):
        """
        List all carbon emission factors.
        ---
        description: Retrieve all carbon emission factors by country.
        tags:
          - Carbon
        responses:
          200:
            description: List of all carbon emission factors
            content:
              application/json:
                schema:
                  type: array
                  items:
                    type: object
                    properties:
                      country_code:
                        type: string
                        description: ISO 3166-1 alpha-2 country code
                        example: FR
                      country_name:
                        type: string
                        description: Country name
                        example: France
                      rendering_co2e:
                        type: number
                        description: CO2e grams per hour for rendering
                        example: 12.0
                      workbench_co2e:
                        type: number
                        description: CO2e grams per hour for workbench
                        example: 10.0
        """
        factors = CarbonFactor.query.all()
        return [f.present() for f in factors]

    @jwt_required()
    def post(self):
        """
        Create or update a carbon emission factor.
        ---
        description: Create or update a carbon emission factor (admin only).
        tags:
          - Carbon
        requestBody:
          required: true
          content:
            application/json:
              schema:
                type: object
                required:
                  - country_code
                  - country_name
                  - rendering_co2e
                  - workbench_co2e
                properties:
                  country_code:
                    type: string
                    description: ISO 3166-1 alpha-2 country code
                    example: FR
                  country_name:
                    type: string
                    description: Country name
                    example: France
                  rendering_co2e:
                    type: number
                    description: CO2e grams per hour for rendering
                    example: 12.0
                  workbench_co2e:
                    type: number
                    description: CO2e grams per hour for workbench
                    example: 10.0
        responses:
          201:
            description: Carbon factor created or updated successfully
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    country_code:
                      type: string
                    country_name:
                      type: string
                    rendering_co2e:
                      type: number
                    workbench_co2e:
                      type: number
          400:
            description: Invalid input data
        """
        permissions.check_admin_permissions()
        data = request.get_json()
        if not data:
            return {"error": "Request body is required"}, 400

        error = self._validate(data)
        if error:
            return {"error": error}, 400

        factor = services.create_or_update_factor(data)
        return factor.present(), 201

    def _validate(self, data):
        country_code = data.get("country_code", "").upper().strip()
        country_name = data.get("country_name", "")

        if not country_code or len(country_code) != 2:
            return "Invalid country_code"
        if not country_name:
            return "country_name is required"

        try:
            float(data.get("rendering_co2e", 0))
            float(data.get("workbench_co2e", 0))
        except (ValueError, TypeError):
            return "rendering_co2e and workbench_co2e must be numeric"

        return None


class CarbonFactorResource(MethodView):

    @jwt_required()
    def get(self, country_code):
        """
        Get carbon emission factor for a specific country.
        ---
        description: Retrieve carbon emission factor for a specific country.
        tags:
          - Carbon
        parameters:
          - in: path
            name: country_code
            required: true
            schema:
              type: string
            description: ISO 3166-1 alpha-2 country code
            example: FR
        responses:
          200:
            description: Carbon emission factor for the country
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    country_code:
                      type: string
                      example: FR
                    country_name:
                      type: string
                      example: France
                    rendering_co2e:
                      type: number
                      example: 12.0
                    workbench_co2e:
                      type: number
                      example: 10.0
          404:
            description: Country not found
        """
        factor = CarbonFactor.get_by(country_code=country_code.upper())
        if not factor:
            return {"error": "Country not found"}, 404
        return factor.present()


class StudioFootprintResource(MethodView):

    @jwt_required()
    def get(self):
        """
        Get CO2 footprint breakdown by production and task type.
        ---
        description: >
          Retrieve CO2 footprint for the whole studio, broken down by
          production and task type.
        tags:
          - Carbon
        responses:
          200:
            description: CO2 footprint breakdown by production
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    details:
                      type: array
                      items:
                        type: object
                        properties:
                          project_id:
                            type: string
                            format: uuid
                          project_name:
                            type: string
                          task_type_id:
                            type: string
                            format: uuid
                          task_type_name:
                            type: string
                          co2_grams:
                            type: number
                          co2_kg:
                            type: number
                          duration_minutes:
                            type: integer
                    by_task_type:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          co2_kg:
                            type: number
                    by_project:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          co2_kg:
                            type: number
                    total_co2_kg:
                      type: number
                    total_duration_minutes:
                      type: integer
                    total_man_days:
                      type: number
        """
        data = services.get_studio_footprint_data()
        weekly = services.get_weekly_change()

        return {
            "details": data["details"],
            "by_task_type": data["by_task_type"],
            "by_project": data["by_project"],
            "total_co2_kg": round(data["total_co2_grams"] / 1000, 4),
            "total_duration_minutes": data["total_duration_minutes"],
            "total_man_days": round(data["total_duration_minutes"] / 60 / 8, 2),
            "weekly_change_percent": weekly["percent_change"],
        }


class ProductionSequenceFootprintResource(MethodView, ArgsMixin):

    @jwt_required()
    def get(self, project_id):
        """
        Get CO2 footprint breakdown by sequence and task type.
        ---
        description: >
          Retrieve CO2 footprint for a production, broken down by sequence
          and task type. Best suited for feature films and shorts.
        tags:
          - Carbon
        parameters:
          - in: path
            name: project_id
            required: true
            schema:
              type: string
              format: uuid
            description: The project ID
            example: a24a6ea4-ce75-4665-a070-57453082c25
        responses:
          200:
            description: CO2 footprint breakdown by sequence
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    project_id:
                      type: string
                      format: uuid
                    project_name:
                      type: string
                    details:
                      type: array
                      items:
                        type: object
                        properties:
                          sequence_id:
                            type: string
                            format: uuid
                          sequence_name:
                            type: string
                          task_type_id:
                            type: string
                            format: uuid
                          task_type_name:
                            type: string
                          co2_grams:
                            type: number
                          co2_kg:
                            type: number
                          duration_minutes:
                            type: integer
                    by_task_type:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          co2_kg:
                            type: number
                    by_sequence:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          co2_kg:
                            type: number
                    total_co2_kg:
                      type: number
                    total_duration_minutes:
                      type: integer
                    total_man_days:
                      type: number
          404:
            description: Project not found
        """
        self.check_id_parameter(project_id)
        user_service.check_project_access(project_id)
        project = projects_service.get_project(project_id)

        data = services.get_sequence_footprint_data(project_id)

        return {
            "project_id": project_id,
            "project_name": project.get("name", ""),
            "details": data["details"],
            "by_task_type": data["by_task_type"],
            "by_sequence": data["by_sequence"],
            "total_co2_kg": round(data["total_co2_grams"] / 1000, 4),
            "total_duration_minutes": data["total_duration_minutes"],
            "total_man_days": round(data["total_duration_minutes"] / 60 / 8, 2),
        }


class ProductionEpisodeFootprintResource(MethodView, ArgsMixin):

    @jwt_required()
    def get(self, project_id):
        """
        Get CO2 footprint breakdown by episode and task type.
        ---
        description: >
          Retrieve CO2 footprint for a TV series production, broken down
          by episode and task type.
        tags:
          - Carbon
        parameters:
          - in: path
            name: project_id
            required: true
            schema:
              type: string
              format: uuid
            description: The project ID
            example: a24a6ea4-ce75-4665-a070-57453082c25
        responses:
          200:
            description: CO2 footprint breakdown by episode
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    project_id:
                      type: string
                      format: uuid
                    project_name:
                      type: string
                    details:
                      type: array
                      items:
                        type: object
                        properties:
                          episode_id:
                            type: string
                            format: uuid
                          episode_name:
                            type: string
                          task_type_id:
                            type: string
                            format: uuid
                          task_type_name:
                            type: string
                          co2_grams:
                            type: number
                          co2_kg:
                            type: number
                          duration_minutes:
                            type: integer
                    by_task_type:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          co2_kg:
                            type: number
                    by_episode:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          co2_kg:
                            type: number
                    total_co2_kg:
                      type: number
                    total_duration_minutes:
                      type: integer
                    total_man_days:
                      type: number
          404:
            description: Project not found
        """
        self.check_id_parameter(project_id)
        user_service.check_project_access(project_id)
        project = projects_service.get_project(project_id)

        data = services.get_episode_footprint_data(project_id)

        return {
            "project_id": project_id,
            "project_name": project.get("name", ""),
            "details": data["details"],
            "by_task_type": data["by_task_type"],
            "by_episode": data["by_episode"],
            "total_co2_kg": round(data["total_co2_grams"] / 1000, 4),
            "total_duration_minutes": data["total_duration_minutes"],
            "total_man_days": round(data["total_duration_minutes"] / 60 / 8, 2),
        }


class ProductionAssetFootprintResource(MethodView, ArgsMixin):

    @jwt_required()
    def get(self, project_id):
        """
        Get CO2 footprint breakdown by asset type and task type.
        ---
        description: >
          Retrieve CO2 footprint for a production, broken down by asset type
          and task type. Works for all production types.
        tags:
          - Carbon
        parameters:
          - in: path
            name: project_id
            required: true
            schema:
              type: string
              format: uuid
            description: The project ID
            example: a24a6ea4-ce75-4665-a070-57453082c25
        responses:
          200:
            description: CO2 footprint breakdown by asset type
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    project_id:
                      type: string
                      format: uuid
                    project_name:
                      type: string
                    details:
                      type: array
                      items:
                        type: object
                        properties:
                          asset_type_id:
                            type: string
                            format: uuid
                          asset_type_name:
                            type: string
                          task_type_id:
                            type: string
                            format: uuid
                          task_type_name:
                            type: string
                          co2_grams:
                            type: number
                          co2_kg:
                            type: number
                          duration_minutes:
                            type: integer
                    by_task_type:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          co2_kg:
                            type: number
                    by_asset_type:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          co2_kg:
                            type: number
                    total_co2_kg:
                      type: number
                    total_duration_minutes:
                      type: integer
                    total_man_days:
                      type: number
          404:
            description: Project not found
        """
        self.check_id_parameter(project_id)
        user_service.check_project_access(project_id)
        project = projects_service.get_project(project_id)

        data = services.get_asset_footprint_data(project_id)

        return {
            "project_id": project_id,
            "project_name": project.get("name", ""),
            "details": data["details"],
            "by_task_type": data["by_task_type"],
            "by_asset_type": data["by_asset_type"],
            "total_co2_kg": round(data["total_co2_grams"] / 1000, 4),
            "total_duration_minutes": data["total_duration_minutes"],
            "total_man_days": round(data["total_duration_minutes"] / 60 / 8, 2),
        }


class ProductionTaskTypeFootprintResource(MethodView, ArgsMixin):

    @jwt_required()
    def get(self, project_id):
        """
        Get CO2 footprint breakdown by task type.
        ---
        description: >
          Retrieve CO2 footprint for a production grouped by task type.
          Simple view without sequence/episode/asset breakdown.
        tags:
          - Carbon
        parameters:
          - in: path
            name: project_id
            required: true
            schema:
              type: string
              format: uuid
            description: The project ID
        responses:
          200:
            description: CO2 footprint breakdown by task type
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    project_id:
                      type: string
                      format: uuid
                    project_name:
                      type: string
                    details:
                      type: array
                      items:
                        type: object
                        properties:
                          task_type_id:
                            type: string
                            format: uuid
                          task_type_name:
                            type: string
                          co2_grams:
                            type: number
                          co2_kg:
                            type: number
                          duration_minutes:
                            type: integer
                    total_co2_kg:
                      type: number
                    total_duration_minutes:
                      type: integer
                    total_man_days:
                      type: number
          404:
            description: Project not found
        """
        self.check_id_parameter(project_id)
        user_service.check_project_access(project_id)
        project = projects_service.get_project(project_id)

        data = services.get_task_type_footprint_data(project_id)
        weekly = services.get_weekly_change(project_id)

        return {
            "project_id": project_id,
            "project_name": project.get("name", ""),
            "details": data["details"],
            "total_co2_kg": round(data["total_co2_grams"] / 1000, 4),
            "total_duration_minutes": data["total_duration_minutes"],
            "total_man_days": round(data["total_duration_minutes"] / 60 / 8, 2),
            "weekly_change_percent": weekly["percent_change"],
        }


class ProductionFootprintSummaryResource(MethodView, ArgsMixin):

    @jwt_required()
    def get(self, project_id):
        """
        Get total CO2 footprint summary for a production.
        ---
        description: >
          Retrieve overall CO2 footprint summary including total emissions,
          man days, and weekly averages.
        tags:
          - Carbon
        parameters:
          - in: path
            name: project_id
            required: true
            schema:
              type: string
              format: uuid
            description: The project ID
            example: a24a6ea4-ce75-4665-a070-57453082c25
        responses:
          200:
            description: CO2 footprint summary
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    project_id:
                      type: string
                      format: uuid
                    project_name:
                      type: string
                    total_co2_kg:
                      type: number
                      description: Total CO2 emissions in kilograms
                    total_duration_minutes:
                      type: integer
                      description: Total work time in minutes
                    total_man_days:
                      type: number
                      description: Total work time in man days (8h/day)
                    weekly_average_co2_kg:
                      type: number
                      description: Average weekly CO2 emissions in kilograms
                    num_weeks_with_data:
                      type: integer
                      description: Number of weeks with time entries
          404:
            description: Project not found
        """
        self.check_id_parameter(project_id)
        user_service.check_project_access(project_id)
        project = projects_service.get_project(project_id)

        data = services.get_summary_footprint_data(project_id)

        return {
            "project_id": project_id,
            "project_name": project.get("name", ""),
            "total_co2_kg": round(data["total_co2_grams"] / 1000, 4),
            "total_duration_minutes": data["total_duration_minutes"],
            "total_man_days": round(data["total_duration_minutes"] / 60 / 8, 2),
            "weekly_average_co2_kg": round(
                data["weekly_average_co2_grams"] / 1000, 4
            ),
            "num_weeks_with_data": data["num_weeks_with_data"],
        }
