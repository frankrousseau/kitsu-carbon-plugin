from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


# CO2e emission factors by country (g CO2e per hour)
# Source: IEA emission factors + typical workstation power consumption
CARBON_FACTORS_DATA = [
    ("AU", "Australia", 150.0, 85.0),
    ("BE", "Belgium", 35.0, 25.0),
    ("BR", "Brazil", 20.0, 15.0),
    ("CA", "Canada", 25.0, 20.0),
    ("CN", "China", 180.0, 100.0),
    ("DE", "Germany", 80.0, 50.0),
    ("DK", "Denmark", 25.0, 18.0),
    ("ES", "Spain", 50.0, 35.0),
    ("FI", "Finland", 20.0, 15.0),
    ("FR", "France", 12.0, 10.0),
    ("GB", "United Kingdom", 55.0, 38.0),
    ("IN", "India", 200.0, 110.0),
    ("IT", "Italy", 70.0, 45.0),
    ("JP", "Japan", 120.0, 70.0),
    ("KR", "South Korea", 130.0, 75.0),
    ("MX", "Mexico", 100.0, 60.0),
    ("NL", "Netherlands", 75.0, 48.0),
    ("NO", "Norway", 8.0, 6.0),
    ("NZ", "New Zealand", 25.0, 18.0),
    ("PL", "Poland", 180.0, 100.0),
    ("SE", "Sweden", 10.0, 8.0),
    ("US", "United States", 95.0, 58.0),
    ("ZA", "South Africa", 220.0, 120.0),
]


class CarbonFactor(db.Model, BaseMixin, SerializerMixin):
    """
    Carbon emission factors by country.
    Stores CO2e emission rates for rendering and workbench activities.
    """

    __tablename__ = "plugin_carbon_factors"
    __table_args__ = {"extend_existing": True}

    country_code = db.Column(db.String(2), unique=True, nullable=False)
    country_name = db.Column(db.String(80), nullable=False)
    rendering_co2e = db.Column(db.Float, nullable=False)
    workbench_co2e = db.Column(db.Float, nullable=False)

    @classmethod
    def seed_initial_data(cls):
        """
        Seed the database with initial carbon factor data for 23 countries.
        """
        for code, name, rendering, workbench in CARBON_FACTORS_DATA:
            existing = (
                db.session.query(cls).filter_by(country_code=code).first()
            )
            if not existing:
                factor = cls(
                    country_code=code,
                    country_name=name,
                    rendering_co2e=rendering,
                    workbench_co2e=workbench,
                )
                db.session.add(factor)
        db.session.commit()
