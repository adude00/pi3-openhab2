# Repository context

- This checkout is the `openhab_conf` volume of a deployed OpenHAB installation, not the full deployment or an application source tree. `docker-compose.yml` pins the runtime version (currently 5.1.4); do not infer it from the historical `openhab2` repository name.
- Compose's relative volumes are rooted in the **deployment directory**, documented as `/opt/docker/openhab5`, which contains `openhab_conf`, `openhab_userdata`, `openhab_addons`, `openhab-init.d`, and `openhab-ssh`. Do not run Compose from this checkout with default path resolution: it would target the wrong directories. Use the real deployment directory or explicitly set `--project-directory` to it.
- This runtime uses host networking and site-specific LAN addresses. Starting it is not an isolated test: rules and scripts control physical devices and can reboot/shut down remote hosts.

# Configuration wiring

- Automations use OpenHAB Rules DSL (`rules/*.rules`), not JavaScript rules. JavaScript in `transform/` runs inside OpenHAB's transformation runtime (`input`, Java interop), not Node.js.
- Trace device changes across Thing channel UIDs, Item channel links, rules, and `sitemaps/default.sitemap`; Item names and MQTT topics are cross-file interfaces. Most MQTT devices and MQTT rule actions use `mqtt:broker:brokerv2`.
- Legacy copies (`.thingo`, `.itemo`, `.old-rulo`, `.persist.disable`, `.dpkg-old`, `.dpkg-dist`, and collections such as `disabled/`, `disabilitati/`, `transformed/`, `backup/`, and `OLD_documents/`) are historical context, not current configuration. Ignore them unless history is relevant; do not reactivate them or create similar backup/versioned copies. Edit current files in place and use Git for version history.
- Boot-only logic belongs in `rules/startup.rules`, using `System reached start level 100`; its delayed notification allows Items and brokers to finish loading.
- Keep add-on lists in `services/addons.cfg` commented. Its local warnings explain that explicit lists remove unlisted UI-managed add-ons at boot. Installed add-ons and UI-managed settings are not fully represented by this repository.

# Persistence

- Active persistence configuration is in `persistence/`; disabled `.persist.disable` files are archived in `OLD_documents/persistence/` for historical reference only.
- Trust the active `.persist` files over stale comments and the archived `OLD_documents/persistence-README.md`: MapDB stores **all Items on every change and restores on startup**; InfluxDB samples selected groups every minute and `gEnergyYesterday*` daily.
- The current persistence README documents InfluxDB as the UI-configured default for history queries; `services/runtime.cfg` does not set it. Do not restore the old rrd4j-default setup or uncomment `Strategies { default = ... }` (deprecated in OpenHAB 5.1).
- Group membership controls InfluxDB coverage (`group*` selects members). When adding Items used by history/average queries, check `persistence/influxdb.persist` as well as their group assignments.

# Scripts and verification

- There is no repository build, automated test suite, lint task, or CI workflow. For a changed Bash helper, use `bash -n path/to/script.sh` rather than executing it; many helpers issue live SSH/HTTP/device commands.
- On the deployment host, inspect the runtime with `docker exec -it openhab5 /openhab/runtime/bin/client` (Karaf console) or `docker exec -it openhab5 /bin/bash`. Runtime validation requires the installed bindings/services and site network; inspect `openhab_userdata/logs/openhab.log` and `events.log` in the deployment directory for configuration errors and behavior.
- Script paths inside the container are `/openhab/conf/scripts/...`. Exec-binding/transformation commands must also match entries in `misc/exec.whitelist`; do not confuse that whitelist with direct Rules DSL `executeCommandLine` calls.
- `shell/bsXX.sh` generates BLE Thing/Item files from templates and **overwrites** its targets. Run only when requested, from `shell/`, as `bash bsXX.sh <bsNN> <MAC-without-separators>`; it also runs `chown openhab.` and needs corresponding permissions.
- SSH keys and extra packages (`openssh-client`, `wakeonlan`, `jq`) come from deployment-side mounts/init scripts described in `README.md`, not tracked setup files here. Keep ignored credentials out of Git: `prowl.cfg`, `influxdb.cfg`, and `scripts/ConnectLife/bearer.sh`.
