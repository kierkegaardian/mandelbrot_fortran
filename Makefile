FC = gfortran
PYTHON ?= python3
FFLAGS = -O3 -Wall -cpp -fPIE -ffree-line-length-none
LDFLAGS =
SRC_DIR = src
BUILD_DIR = build
TARGET = mandelbrot_gen
PPM ?= mandelbrot.ppm
PNG ?= mandelbrot.png

OPENMP ?= 1
ifeq ($(OPENMP),1)
FFLAGS += -fopenmp
endif

SOURCES = $(SRC_DIR)/cli.f90 $(SRC_DIR)/ppm_writer.f90 $(SRC_DIR)/mandelbrot.f90
OBJECTS = $(SOURCES:$(SRC_DIR)/%.f90=$(BUILD_DIR)/%.o)
MODULES = $(BUILD_DIR)/*.mod

all: preflight $(TARGET)

preflight:
	@command -v $(FC) >/dev/null 2>&1 || (echo "Error: '$(FC)' not found. Install gfortran (Arch: sudo pacman -S gcc-fortran)."; exit 1)

$(TARGET): $(BUILD_DIR) $(OBJECTS)
	$(FC) $(FFLAGS) $(LDFLAGS) -o $@ $(OBJECTS)

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.f90
	$(FC) $(FFLAGS) -J$(BUILD_DIR) -c $< -o $@

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR) $(TARGET) *.ppm

run: all
	./$(TARGET)

png: all
	@command -v magick >/dev/null 2>&1 || (echo "Error: ImageMagick 'magick' not found. Install imagemagick or use PPM output."; exit 1)
	./$(TARGET) --output $(PPM)
	magick $(PPM) $(PNG)

test:
	$(PYTHON) -m tests.run_isolated

check: all test

DOCKER ?= docker
DOCKER_IMAGE ?= gcc:14
DOCKER_RUN = $(DOCKER) run --rm --user $$(id -u):$$(id -g) -v "$(CURDIR)":/work -w /work $(DOCKER_IMAGE)

docker-build:
	@$(DOCKER_RUN) bash -lc "make clean >/dev/null 2>&1 || true; make"

docker-run: docker-build
	@$(DOCKER_RUN) bash -lc "./$(TARGET)"

docker-run-omp:
	@$(DOCKER_RUN) bash -lc "make clean >/dev/null 2>&1 || true; make OPENMP=1 && ./$(TARGET) --threads 8 --progress-every 0 --output mandelbrot_omp.ppm"

.PHONY: all clean run png test check preflight docker-build docker-run docker-run-omp
