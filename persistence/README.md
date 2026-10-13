# Persistence

This installation uses two persistence services: MapDB and InfluxDB.
Services are installed and configured through the OpenHAB UI.

## MapDB: restore Item states

`mapdb.persist` stores the latest state of every Item on each change
and restores it at startup.

MapDB does not retain historical values or update timestamps. It
preserves Item states across restarts, including user-configured
settings.

## InfluxDB: history and graphs

InfluxDB is configured as the default persistence service through
the OpenHAB UI, allowing rules to query history without specifying
a service.

`influxdb.persist` records:

- Members of the listed groups every minute.
- Members of `gEnergyYesterday` daily at midnight.

In persistence configuration, `group*` means the group's members.
When adding an Item that needs history, include it in a group listed
in `influxdb.persist`.

InfluxDB does not restore Item states at startup in this configuration;
MapDB handles restoration.

## Configuration notes

- Persistence strategies are assigned explicitly in each `.persist` file.
  Do not add a default strategy: it was deprecated in OpenHAB 5.1.
- Disabled persistence files are archived in
  [`OLD_documents/persistence/`](../OLD_documents/persistence/), not active
  configuration. Use Git for history rather than creating new copies.
- Database connection settings and the default persistence selection
  are not fully represented by this repository.

## Historical reference

The [previous README](../OLD_documents/persistence-README.md) is preserved
for reference only; it includes obsolete configuration instructions.
