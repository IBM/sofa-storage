MODULE := sofa_storage
EXAMPLE_MODULE := example

BLUE=\033[0;34m
NC=\033[0m # No Color

run:
	@python -m $(MODULE).dpu_server

test:
	@pytest

lint:
	@echo "${BLUE}Running Pylint against source and test files...${NC}"
	@pylint --rcfile=setup.cfg **/*.py
	@echo "${BLUE}Running Flake8 against source and test files...${NC}"
	@flake8
	@echo "${BLUE}Running Bandit against source files...${NC}"
	@bandit -r --ini setup.cfg

grpc-gen:
	@python -m grpc_tools.protoc \
			-I $(MODULE)/proto \
			--python_out=./$(MODULE)/generated \
			--grpc_python_out=./$(MODULE)/generated \
			./$(MODULE)/proto/*.proto
	@sed -i -E 's/^import.*_pb2/from . \0/' ./$(MODULE)/generated/*.py

example-run:
	@python -m $(EXAMPLE_MODULE).ctrl_server

example-grpc-gen:
	@python -m grpc_tools.protoc \
			-I $(EXAMPLE_MODULE)/proto \
			--python_out=./$(EXAMPLE_MODULE)/generated \
			--grpc_python_out=./$(EXAMPLE_MODULE)/generated \
			./$(EXAMPLE_MODULE)/proto/*.proto
	@sed -i -E 's/^import.*_pb2/from . \0/' ./$(EXAMPLE_MODULE)/generated/*.py

clean:
	rm -rf .pytest_cache .coverage .pytest_cache coverage.xml