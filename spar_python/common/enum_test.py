# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Unit tests for the Enum class. 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  07 Dec 2011   omd            Original Version
# *****************************************************************

import unittest
from enum import Enum

class EnumTest(unittest.TestCase):
    def test_basic(self):
        """Test the most basic usage."""
        ANIMALS = Enum('CAT', 'DOG', 'TIGER', 'WOLF')
        self.assertEqual(ANIMALS.CAT, 0)
        self.assertEqual(ANIMALS.DOG, 1)
        self.assertEqual(ANIMALS.TIGER, 2)
        self.assertEqual(ANIMALS.WOLF, 3)

    def test_selected_integers(self):
        """Test that user-defined integer assignements work."""
        ANIMALS = Enum(CAT = 10, DOG = 22, TIGER = 3, WOLF = 7)
        self.assertEqual(ANIMALS.CAT, 10)
        self.assertEqual(ANIMALS.DOG, 22)
        self.assertEqual(ANIMALS.TIGER, 3)
        self.assertEqual(ANIMALS.WOLF, 7)

    def test_mixed_selected_assigned_integers(self):
        """Test that you can mix specified mappings from integer to value and
        just a list of values and it works right."""
        ANIMALS = Enum('DOG', 'CAT', 'WOLF', HAMSTER = 0, RABBIT = 2,
                WHALE = 100)
        self.assertEqual(ANIMALS.HAMSTER, 0)
        self.assertEqual(ANIMALS.DOG, 1)
        self.assertEqual(ANIMALS.RABBIT, 2)
        self.assertEqual(ANIMALS.CAT, 3)
        self.assertEqual(ANIMALS.WOLF, 4)
        self.assertEqual(ANIMALS.WHALE, 100)

    def test_to_string(self):
        """Uses the same enum as test_mixed_selected_assigned_integers and tests
        that we can map from integer back to string."""
        ANIMALS = Enum('DOG', 'CAT', 'WOLF', HAMSTER = 0, RABBIT = 2,
                WHALE = 100)
        self.assertEqual(ANIMALS.to_string(0), 'HAMSTER')
        self.assertEqual(ANIMALS.to_string(1), 'DOG')
        self.assertEqual(ANIMALS.to_string(2), 'RABBIT')
        self.assertEqual(ANIMALS.to_string(3), 'CAT')
        self.assertEqual(ANIMALS.to_string(4), 'WOLF')
        self.assertEqual(ANIMALS.to_string(100), 'WHALE')

    def test_to_string_lower(self):
        """Uses the same enum as test_mixed_selected_assigned_integers and tests
        that we can map from integer back to string."""
        ANIMALS = Enum('DOG', 'CAT', 'WOLF', HAMSTER = 0, RABBIT = 2,
                WHALE = 100)
        self.assertEqual(ANIMALS.to_string_lower(0), 'HAMSTER'.lower())
        self.assertEqual(ANIMALS.to_string_lower(1), 'DOG'.lower())
        self.assertEqual(ANIMALS.to_string_lower(2), 'RABBIT'.lower())
        self.assertEqual(ANIMALS.to_string_lower(3), 'CAT'.lower())
        self.assertEqual(ANIMALS.to_string_lower(4), 'WOLF'.lower())
        self.assertEqual(ANIMALS.to_string_lower(100), 'WHALE'.lower())

    def test_constant(self):
        """An enum should be constant. Try to modify it in various ways and make
        sure it doesn't change."""
        ANIMALS = Enum('DOG', 'CAT', 'WOLF', HAMSTER = 0, RABBIT = 2,
                WHALE = 100)
        with self.assertRaises(ValueError):
            del(ANIMALS.DOG)

        with self.assertRaises(ValueError):
            ANIMALS.CAT = 222

    def test_generate_string(self):
        """Test the values_generator method."""
        ANIMALS = Enum('DOG', 'CAT', 'WOLF', HAMSTER = 0, RABBIT = 2,
                WHALE = 100)
        expected = ['HAMSTER', 'DOG', 'RABBIT', 'CAT', 'WOLF', 'WHALE']
        expected_index = 0
        for val in ANIMALS.values_generator():
            self.assertEqual(val, expected[expected_index])
            expected_index += 1

    def test_generate_numbers(self):
        """Test the numbers_generator method."""
        ANIMALS = Enum('DOG', 'CAT', 'WOLF', HAMSTER = 0, RABBIT = 2,
                WHALE = 100)
        expected = [0, 1, 2, 3, 4, 100]
        expected_index = 0
        for i in ANIMALS.numbers_generator():
            self.assertEqual(i, expected[expected_index])
            expected_index += 1

    def test_from_dict_list(self):
        """Test that the from_dict_list factory method works."""
        E_NORMAL = Enum('DOG', 'CAT', HAMSTER = 1)
        E_FACTORY = Enum.from_dict_list({'HAMSTER': 1}, ['DOG', 'CAT'])
        self.assertEqual(E_FACTORY.DOG, E_NORMAL.DOG)
        self.assertEqual(E_FACTORY.CAT, E_NORMAL.CAT)
        self.assertEqual(E_FACTORY.HAMSTER, E_NORMAL.HAMSTER)
        self.assertEqual(E_FACTORY.numbers_list(), E_NORMAL.numbers_list())
        for f, n in zip(E_FACTORY.values_generator(),
                E_NORMAL.values_generator()):
            self.assertEqual(f, n)
        # zip tries to handle generators that produce different numbers of items
        # so we double check that they're both the same size here.
        self.assertEqual(len([x for x in E_FACTORY.values_generator()]),
                len([x for x in E_NORMAL.values_generator()]))

    def test_from_enum(self):
        BASE = Enum('DOG', CAT = 3, HORSE = 5)
        NEW = Enum.from_enum(BASE, 'HAMSTER', 'RAT', 'MOUSE', SNAKE = 6,
                DONKEY = 11)

        self.assertEqual(NEW.DOG, 0)
        self.assertEqual(NEW.HAMSTER, 1)
        self.assertEqual(NEW.RAT, 2)
        self.assertEqual(NEW.CAT, 3)
        self.assertEqual(NEW.MOUSE, 4)
        self.assertEqual(NEW.HORSE, 5)
        self.assertEqual(NEW.SNAKE, 6)
        self.assertEqual(NEW.DONKEY, 11)

    def test_from_enum_collisions(self):
        """Make sure that an exception gets thrown if we try to create an enum
        via from_enum but there are collisions in the requested values."""
        BASE = Enum('CAR', 'BIKE', SCOOTER = 5)

        # Try to create new enums but with numerical values that already exist
        # in the base enum. This should cause an exception.
        with self.assertRaises(ValueError):
            NEW = Enum.from_enum(BASE, AIRPLANE = 1)

        with self.assertRaises(ValueError):
            NEW3 = Enum.from_enum(BASE, AIRPLANE = 0)

        with self.assertRaises(ValueError):
            NEW4 = Enum.from_enum(BASE, AIRPLANE = 5)

        with self.assertRaises(ValueError):
            NEW5 = Enum.from_enum(BASE, 'TRAIN', AIRPLANE = 5)

        # Try to create new enums but with names that already exist in the base
        # enum (though with different numerical values). This should cause an
        # exception.
        with self.assertRaises(ValueError):
            NEW6 = Enum.from_enum(BASE, 'CAR')

        with self.assertRaises(ValueError):
            NEW7 = Enum.from_enum(BASE, BIKE = 11)

