# UFPS Development Makefile
# Convenient commands for development and testing

.PHONY: help install uninstall test test-clean test-docker test-quick clean dev-install

# Default target
help:
	@echo "UFPS Development Commands"
	@echo "========================="
	@echo ""
	@echo "Installation:"
	@echo "  make install      - Install UFPS"
	@echo "  make uninstall    - Uninstall UFPS"
	@echo "  make dev-install  - Install in development mode"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run installation tests (preserves existing)"
	@echo "  make test-clean   - Run tests with clean installation"
	@echo "  make test-quick   - Run quick tests only"
	@echo "  make test-docker  - Run tests in Docker container"
	@echo "  make test-all     - Run all test variations"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean        - Remove temporary files"
	@echo "  make reset        - Complete reset (uninstall + clean)"

# Installation targets
install:
	@echo "Installing UFPS..."
	@python3 install.py

uninstall:
	@echo "Uninstalling UFPS..."
	@echo "y" | python3 uninstall.py

dev-install:
	@echo "Installing UFPS in development mode..."
	@python3 install.py --dev

# Testing targets
test:
	@echo "Running installation tests..."
	@python3 test_install.py --verbose

test-clean:
	@echo "Running clean installation tests..."
	@python3 test_install.py --clean --verbose

test-quick:
	@echo "Running quick tests..."
	@python3 test_install.py --quick

test-docker:
	@echo "Running Docker-based tests..."
	@chmod +x docker-test.sh
	@./docker-test.sh

test-all: test test-clean test-docker
	@echo "All tests completed!"

# Maintenance targets
clean:
	@echo "Cleaning temporary files..."
	@rm -rf __pycache__ *.pyc
	@rm -rf ufps/__pycache__ ufps/*.pyc
	@rm -rf .pytest_cache
	@rm -rf build dist *.egg-info
	@rm -f /tmp/ufps_*.txt /tmp/ufps_*.log
	@echo "Clean complete!"

reset: uninstall clean
	@echo "Full reset complete!"

# Development helpers
check-deps:
	@echo "Checking dependencies..."
	@which python3 || echo "❌ Python 3 not found"
	@which git || echo "❌ Git not found"
	@which ffmpeg || echo "❌ FFmpeg not found"
	@python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" || echo "❌ Python 3.8+ required"

# Watch for changes and auto-test (requires entr)
watch:
	@echo "Watching for changes..."
	@find . -name "*.py" | entr -c make test-quick

# Create test video for testing
create-test-video:
	@echo "Creating test video..."
	@ffmpeg -f lavfi -i testsrc=duration=5:size=320x240:rate=30 \
	        -f lavfi -i sine=frequency=1000:duration=5 \
	        -pix_fmt yuv420p test_video.mp4 2>/dev/null
	@echo "Created test_video.mp4 (30fps, 5 seconds)"

# Benchmarking
benchmark:
	@echo "Running performance benchmark..."
	@time python3 -c "from ufps.core import process_video; \
	                  process_video('test_video.mp4', 'output.mp4', scale=2, target_fps=60)"