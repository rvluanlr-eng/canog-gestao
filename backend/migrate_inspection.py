"""Create the new inspection table in an existing CANOG database without modifying other tables.
Run once with the same DATABASE_URL as the API, after taking a database backup.
"""
from main import engine, DeviceInspection
DeviceInspection.__table__.create(bind=engine,checkfirst=True)
print('Tabela device_inspections disponível.')
