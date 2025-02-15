#!/bin/bash
APP_ID := underwaterreport
APP_NAME := UnderwaterReport
APP_VERSION := 1.0.0
APP_SECRET := 12345
APP_PORT := 9031
GITHUB_USERNAME := marwisopot

JSON_INFO := "{\"id\":\"$(APP_ID)\",\"name\":\"$(APP_NAME)\",\"daemon_config_name\":\"manual_install\",\"version\":\"$(APP_VERSION)\",\"secret\":\"$(APP_SECRET)\",\"port\":$(APP_PORT),\"routes\":[{\"url\":\".*\",\"verb\":\"GET, POST, PUT, DELETE\",\"access_level\":1,\"headers_to_exclude\":[]}]}"

sudo -u www-data php occ app_api:app:unregister $(APP_ID) --silent --force || true
sudo -u www-data php occ app_api:app:register $(APP_ID) manual_install --json-info $(JSON_INFO) --wait-finish
