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


def generate_email(first_name: str, last_name: str, school_domain='PSU.EDU', seed: Optional[str] = None):
    """
    Generate a realistic PSU teacher email using names and optional seed.
    """
    rng = random.Random(seed)
    initial = first_name[0].lower()
    last_cleaned = re.sub(r'[^a-zA-Z]', '', last_name).lower()
    num = rng.randint(100, 9999)
    return f"{initial}{last_cleaned}{num}@{school_domain}"


def generate_birth_date(seed: Optional[str] = None):
    """
    Generate a realistic teacher birth date (1975-1995) with optional seed.
    """
    rng = random.Random(seed)
    year = rng.randint(1975, 1995)
    month = str(rng.randint(1, 12)).zfill(2)
    day = str(rng.randint(1, 28)).zfill(2)
    return f"{year}-{month}-{day}"

