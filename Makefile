# Thin wrappers so the plugin's nested paths don't have to be typed out.
PLUGIN := plugins/cryptic-setter
PUZZLE ?= $(PLUGIN)/fixtures/first-light-good.json
OUT    ?= dist/puzzle.html

.PHONY: check validate build body clean

## Run the calibration tests: good fixture clean, every planted defect caught.
check:
	python3 $(PLUGIN)/scripts/test_fixtures.py

## Validate every fixture.
validate:
	python3 $(PLUGIN)/scripts/validate.py $(PLUGIN)/fixtures/first-light-good.json \
	                                      $(PLUGIN)/fixtures/behind-bars-good.json
	python3 $(PLUGIN)/scripts/validate.py --expect-fail $(PLUGIN)/fixtures/first-light-bad.json

## Build a standalone page: make build PUZZLE=path/to/puzzle.json
build:
	python3 $(PLUGIN)/scripts/build_ui.py $(PUZZLE) -o $(OUT)

## Build a body for publishing as an Artifact.
body:
	python3 $(PLUGIN)/scripts/build_ui.py $(PUZZLE) --artifact-body -o dist/puzzle-body.html

clean:
	rm -rf dist
