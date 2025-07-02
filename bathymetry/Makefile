SHELL=/bin/bash
MAKEFLAGS += --always-make  ## All targets are PHONY

# MAKEFILE STRUCTURE PULLED FROM:
# https://gist.github.com/rsperl/d2dfe88a520968fbc1f49db0a29345b9

# to see all colors, run
# bash -c 'for c in {0..255}; do tput setaf $c; tput setaf $c | cat -v; echo =$c; done'
# the first 15 entries are the 8-bit colors

# Terminal colors
ifneq (,$(findstring xterm,${TERM}))
	BLACK        := $(shell tput -Txterm setaf 0)
	RED          := $(shell tput -Txterm setaf 1)
	GREEN        := $(shell tput -Txterm setaf 2)
	YELLOW       := $(shell tput -Txterm setaf 3)
	LIGHTPURPLE  := $(shell tput -Txterm setaf 4)
	PURPLE       := $(shell tput -Txterm setaf 5)
	BLUE         := $(shell tput -Txterm setaf 6)
	WHITE        := $(shell tput -Txterm setaf 7)
	RESET := $(shell tput -Txterm sgr0)
else
	BLACK        := ""
	RED          := ""
	GREEN        := ""
	YELLOW       := ""
	LIGHTPURPLE  := ""
	PURPLE       := ""
	BLUE         := ""
	WHITE        := ""
	RESET        := ""
endif

# set target color
TARGET_COLOR := $(BLUE)

POUND = \#

ACOLITE_PATH = ../../acolite

build-env:  ## Builds local Conda environment
	@echo "${TARGET_COLOR}Building Environment...${RESET}"
	@conda init bash
	@conda env create -f environment.yml

install-dependencies:  ## Installs ACOLITE and AROSICS 
	@if cd ${ACOLITE_PATH} && git rev-parse --git-dir > /dev/null 2>&1; then\
		echo "${TARGET_COLOR}ACOLITE already present!${RESET}";\
	else\
		echo "${TARGET_COLOR}ACOLITE NOT present! Downloading!${RESET}";\
		cd ${ACOLITE_PATH} && git clone "https://github.com/acolite/acolite.git" ./;\
	fi

download-soest:  ## Downloads and processes SOEST Hawaii Bathymetry Data to local data directory
	@echo "${TARGET_COLOR}Downloading SOEST Hawaii Bathymetry Data! This may take a long time!${RESET}"
	@curl -L "https://www.soest.hawaii.edu/hmrg/multibeam/all_Hawaii/hawaii_bty_5m.zip" -o data/hawaii_bty_5m.zip
	@echo "${TARGET_COLOR}Unzipping Hawaii Bathymetry Data...${RESET}"
	@unzip -o data/hawaii_bty_5m.zip -d data/hawaii_bty_grid
	@echo "${TARGET_COLOR}Removing Hawaii bathymetry zip file...${RESET}"
	@rm data/hawaii_bty_5m.zip
	@echo "${TARGET_COLOR}Converting ArcGrid to GeoTIFF...${RESET}"
	@gdal_translate data/hawaii_bty_grid/hawaii_bty_5m data/hawaii_bty_grid/hawaii_bty_5m.tif -co "COMPRESS=LZW" -co "BIGTIFF=YES"
	@echo "{$TARGET_COLOR}Removing ArcGrid files...${RESET}"
	@rm -rf data/hawaii_bty_grid/hawaii_bty_5m/
	@echo "{$TARGET_COLOR}SOEST Download & processing complete!${RESET}"

process-datasets:
	@echo "${TARGET_COLOR}Downloading & pre-processing datasets...${RESET}"
	@python scripts/image_processing/main.py

run-experiments:  ## Runs experiments on the processed datasets
	@echo "${TARGET_COLOR}Running experiments...${RESET}"
	@python scripts/ml_funcs.py

setup:
	build-env
	install-dependencies

