import re
import random
from typing import Optional


class NameGenerator:
    """Realistic Name Generator with seeding support"""
    
    FIRST_NAMES = [
        'James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda',
        'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
        'Thomas', 'Sarah', 'Christopher', 'Karen', 'Charles', 'Lisa', 'Daniel', 'Nancy',
        'Matthew', 'Sandra', 'Anthony', 'Betty', 'Mark', 'Ashley', 'Donald', 'Emily',
        'Steven', 'Kimberly', 'Andrew', 'Margaret', 'Paul', 'Donna', 'Joshua', 'Michelle',
        'Kenneth', 'Carol', 'Kevin', 'Amanda', 'Brian', 'Dorothy', 'George', 'Melissa',
        'Timothy', 'Deborah', 'Ronald', 'Stephanie', 'Edward', 'Rebecca', 'Jason', 'Sharon',
        'Jeffrey', 'Laura', 'Ryan', 'Cynthia', 'Jacob', 'Kathleen', 'Gary', 'Amy',
        'Nicholas', 'Angela', 'Eric', 'Shirley', 'Jonathan', 'Anna', 'Stephen', 'Brenda',
        'Larry', 'Pamela', 'Justin', 'Emma', 'Scott', 'Nicole', 'Brandon', 'Helen',
        'Benjamin', 'Samantha', 'Samuel', 'Katherine', 'Gregory', 'Christine', 'Alexander', 'Debra',
        'Frank', 'Rachel', 'Patrick', 'Carolyn', 'Raymond', 'Janet', 'Jack', 'Catherine',
        'Dennis', 'Maria', 'Jerry', 'Heather', 'Tyler', 'Diane', 'Aaron', 'Ruth',
        'Jose', 'Julie', 'Adam', 'Olive', 'Nathan', 'Virginia', 'Henry', 'Kathleen',
        'Douglas', 'Andrea', 'Zachary', 'Hannah', 'Peter', 'Joe', 'Kyle', 'Jordan',
        'Lauren', 'Evelyn', 'Christian', 'Abigail', 'Megan', 'Alice', 'Ethan', 'Julia'
    ]
    
    LAST_NAMES = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas',
        'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
        'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young',
        'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
        'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
        'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker',
        'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales', 'Murphy',
        'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson', 'Bailey',
        'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson',
        'Watson', 'Brooks', 'Chavez', 'Wood', 'James', 'Bennett', 'Gray', 'Mendoza',
        'Ruiz', 'Hughes', 'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers',
        'Long', 'Ross', 'Foster', 'Jimenez', 'Powell', 'Jenkins', 'Perry', 'Russell'
    ]

    @classmethod
    def generate(cls, seed: Optional[str] = None):
        """
        Generate a realistic name, optionally using a seed for consistency.
        """
        rng = random.Random(seed)
        first_name = rng.choice(cls.FIRST_NAMES)
        last_name = rng.choice(cls.LAST_NAMES)
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}"
        }


def generate_email(seed: Optional[str] = None):
    """
    Generate a realistic teacher email with optional seed.
    """
    rng = random.Random(seed)
    name = NameGenerator.generate(seed=seed)
    first_name = name['first_name'].lower()
    last_name = name['last_name'].lower()
    random_num = rng.randint(1000, 9999)
    domains = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'icloud.com']
    domain = rng.choice(domains)
    return f"{first_name}.{last_name}{random_num}@{domain}"


def generate_birth_date(seed: Optional[str] = None):
    """
    Generate a realistic teacher birth date (1970-1990) with optional seed.
    """
    rng = random.Random(seed)
    year = rng.randint(1970, 1990)
    month = str(rng.randint(1, 12)).zfill(2)
    day = str(rng.randint(1, 28)).zfill(2)
    return f"{year}-{month}-{day}"

