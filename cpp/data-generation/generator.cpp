/*
This is the C/C++ extension module to be used by Python to generate fingerprints.
It depends on the fingerprint generator written by Yang.

To use:

import generator

pGen=generator.fingerprintGenerator()
pGen.Initialize(#mean,#sigma) //where #mean and #sigma are int values passed in.
pGen.SetSeed(####) //where #### is some int value
bits=pGen.GetRandomBits()

*/



#include <Python.h>
#include "structmember.h"
#include <vector>

#include "fingerprint-generator.h"
FingerprintGenerator *pGen;


typedef struct {
    PyObject_HEAD
} fingerprintGenerator;

static void
fingerprintGenerator_dealloc(fingerprintGenerator* self)
{
    delete pGen;
    self->ob_type->tp_free((PyObject*)self);
}

static PyObject *
fingerprintGenerator_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    fingerprintGenerator *self;

    self = (fingerprintGenerator *)type->tp_alloc(type, 0);
    return (PyObject *)self;
}

static int
fingerprintGenerator_init(fingerprintGenerator *self, PyObject *args, PyObject *kwds)
{

        
    return 0;
}

static PyMemberDef fingerprintGenerator_members[] = {
   /* {"number", T_INT, offsetof(fingerprintGenerator, number), 0,
     "generator number"},*/
    {NULL}  /* Sentinel */
};


static PyGetSetDef fingerprintGenerator_getseters[] = {
   /* {"first", 
     (getter)fingerprintGenerator_getfirst, (setter)fingerprintGenerator_setfirst,
     "first name",
     NULL},
    {"last", 
     (getter)fingerprintGenerator_getlast, (setter)fingerprintGenerator_setlast,
     "last name",
     NULL},*/
    {NULL}  /* Sentinel */
};

////////////////////////////////////////////////NEW
static PyObject *
fingerprintGenerator_GetRandomBits(fingerprintGenerator* self)
{
  int length;
  char* fingerprint = pGen->GetRandomBits(&length);
	return Py_BuildValue("s#", fingerprint, length);
}



static PyObject *
fingerprintGenerator_Initialize(fingerprintGenerator* self,PyObject *args)
{
	int i,j;
    int ok=PyArg_ParseTuple(args,"ii",&i,&j);
	if(!pGen)
	{
		pGen=new FingerprintGenerator(i,j);
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
fingerprintGenerator_SetSeed(fingerprintGenerator* self,PyObject *args)
{
	int i;
    int ok=PyArg_ParseTuple(args,"i",&i);
    
	if(pGen)
	{
		pGen->SetSeed(i);
	}

	Py_INCREF(Py_None);
	return Py_None;
}
///////////////////////////////////////////////END NEW

static PyMethodDef fingerprintGenerator_methods[] = {
    
	////new
	{"GetRandomBits", (PyCFunction)fingerprintGenerator_GetRandomBits, METH_NOARGS,
     "Return the random bits"
	},
	{"SetSeed", (PyCFunction)fingerprintGenerator_SetSeed, METH_VARARGS,
     "Sets the seed of the boost random number generator"
	},
	{
		"Initialize", (PyCFunction)fingerprintGenerator_Initialize, METH_VARARGS,
		"Initializes the fingerprint generator"
	},
	//end new
    {NULL}  /* Sentinel */
};

static PyTypeObject fingerprintGeneratorType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "generator.fingerprintGenerator",             /*tp_name*/
    sizeof(fingerprintGenerator),             /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)fingerprintGenerator_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "fingerprintGenerator objects",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    fingerprintGenerator_methods,             /* tp_methods */
    0,/*fingerprintGenerator_members,*/             /* tp_members */
    0,/*fingerprintGenerator_getseters,*/           /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)fingerprintGenerator_init,      /* tp_init */
    0,                         /* tp_alloc */
    fingerprintGenerator_new,                 /* tp_new */
};

static PyMethodDef module_methods[] = {
    {NULL}  /* Sentinel */
};

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initgenerator(void) 
{
    PyObject* m;

    if (PyType_Ready(&fingerprintGeneratorType) < 0)
        return;

    m = Py_InitModule3("generator", module_methods,
                       "Wrapper for Fingerprint generator.");

    if (m == NULL)
      return;

    Py_INCREF(&fingerprintGeneratorType);
    PyModule_AddObject(m, "fingerprintGenerator", (PyObject *)&fingerprintGeneratorType);
}

