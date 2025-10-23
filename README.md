# aqt-connector

## License
This software is licensed under the Apache License 2.0, see the [LICENSE file](LICENSE) for details.


## Configuration
### Precedence
1. Command line options
2. Environment variables
3. Configuration file


### Command line options
If you specify an option by using a command line parameter, it overrides any value from either the corresponding environment variable or the configuration file.


### Environment variables
The SDK will read config from any environment variables that start with "AQT_". 

You can override an individual setting by using a command line parameter. If you specify an option by using one of the environment variables, it overrides any value loaded from the configuration file.

### Configuration file
The SDK will read config from a config file in TOML format. The SDK expects a single section named `default`.

You can override an individual setting by either setting one of the supported environment variables, or by using a command line parameter.

#### Where is the config file stored?
Windows: `%APPDATA%\aqt\config`

macOS: `~/Library/Preferences/aqt/config`

Linux/Unix: `/.config/aqt/config`


### Supported config settings
| Configuration file setting | Environment variable | Command line option | Description |
|-|-|-|-|
| client_id | AQT_CLIENT_ID | --client-id | If you have been assigned a client ID by AQT, you can enter it here. Most users do not need to set this. Setting this and client_secret causes the client credentials authentication flow to be triggered, otherwise it is ignored. |
| client_secret | AQT_CLIENT_SECRET | --client-secret | If you have been assigned a client secret by AQT, you can enter it here. Most users do not need to set this. Setting this and client_id causes the client credentials authentication flow to be triggered, otherwise it is ignored. |
| arnica_url | - | - | The URL of the Arnica API.  |
| store_access_token | AQT_STORE_ACCESS_TOKEN | - | Disable automatically storing any retrieved access tokens to disk by setting this to an empty string (""). Use this setting if you want to manage persistence of access tokens yourself. Defaults to true, so the token will be stored in the user's config directory. |



