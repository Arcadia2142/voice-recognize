.PHONY: all prepare clean

all: prepare

prepare: clean
	bash install.sh

clean:
	rm -Rf ./venv ./tmp