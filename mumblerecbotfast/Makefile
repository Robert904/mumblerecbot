PLATFORM = MINGW32

ifeq ($(PLATFORM), MINGW32)
	MOD_EXT = pyd
	ADD_FLAGS = -c mingw32
endif
ifeq ($(PLATFORM), UNIX)
	MOD_EXT = so
	ADD_FLAGS = 
endif

MOD_NAME = sound_add

#-------------------------

../$(MOD_NAME).$(MOD_EXT) :
	python setup.py build_ext --inplace $(ADD_FLAGS)
	mv $(MOD_NAME).$(MOD_EXT) ../

clean :
	rm -r build $(MOD_NAME).c $(MOD_NAME).pyd