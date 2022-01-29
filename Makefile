.PHONY: all prepare clean

all: prepare

prepare: clean
	bash install.sh

clean:
	rm -Rf ./tmp
	rm -Rf ./train
	rm -Rf ./recognize