# Eufy RobovVac control for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![Sponsor me on Github Sponsors](https://img.shields.io/badge/Sponsor-ea4aaa?style=for-the-badge&logo=github-sponsors&logoColor=%23EA4AAA&labelColor=white)](https://github.com/sponsors/damacus)

A Eufy RoboVac integration for Home Assistant that includes a Config Flow to add your RoboVac(s) and the local key and ID required. All you need to do is enter your Eufy app credentials and the Config Flow will look up the details for you. After the initial config use the configuration button on the Integration to enter the RoboVac IP address when prompted.

## History

This work has evolved from the original work by [Richard Mitchell](https://github.com/mitchellrj) and the countless others who have contributed over the last couple of years. It also builds on the work done by [Andre Borie](https://gitlab.com/Rjevski/eufy-device-id-and-local-key-grabber) to get the required local ID and key.

This is yet another Eufy fork, this time based on work from [CodeFoodPixels](https://github.com/CodeFoodPixels).

## Installation

### Prerequisites

1. Make sure your Home Assistant Core is up to date
2. Remove any previous Eufy or RoboVac installation including entries in the configuration.yaml

### Using HACS

1. In HACS add this repo as an integration additional repository.
2. Then install it.
3. Restart Home Assistant
4. Go to the Integrations Page and Click +Add Integration button
5. Search for Eufy RoboVac and select it
6. Enter your Eufy username and password (The ones you use to login to the add with) and submit
7. If youve done it correctly you should get a success dialoge and option to enter an Area for each RoboVac you have
8. Click Finish
9. On the Integrations Screen Locate your Eufy RoboVac card and click the configure button
10. Select the Radio button beside the Vacuum name and type its IP addess in the box and press Submit
(You need to repeat steps 9 and 10 for each RoboVac you have)
11. Enjoy

Please note: You may have to get a new version of the access key for your vacuum from time to time if Eufy change it. Worst case you have to Delete the integration and re add it to get the new key.

## Debugging

The integration includes debug logging statements that can provide valuable insights into component operations. These logs can be accessed through the Home Assistant System Log.

For real-time log monitoring, consider using the Log Viewer Add-on available in the Home Assistant store.

To enable detailed debug logging, add the following configuration to your `configuration.yaml` file:

```yaml
logger:
  default: warning
  logs:
    custom_components.robovac.vacuum: debug
    custom_components.robovac.tuyalocalapi: debug
```
