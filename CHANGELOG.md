# Changelog

## unreleased

## aqt-connector 0.4.0
* Function to (blockingly) await for the final result of a job #13
* Description regarding access tokens storage and expiration in README #14
* The caller of the wait_for_final_state function can stay updated about the job state during polling #19
* Add context manager to close http clients #23
* Improve validation logic for measurement operations in circuits #29
* Remove support for Python 3.9, add support for Python 3.14. Update dependencies #32

## aqt-connector 0.3.0
* Increase circuit qubit limit to <=31 #11

## aqt-connector 0.2.0
* Add fetch job state #8
* Add Arnica API schemas and update the models #4

## aqt-connector 0.1.0
* Add license and changelog. Update pyproject.toml #3
* Move py.typed to correct location in package directory #1 
* Initial version