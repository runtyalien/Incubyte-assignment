"""Name pools per country, so the Bangalore office doesn't read as Ohio.

Small lists on purpose. Repeats across 10,000 people are realistic, and
uniqueness is carried by the staff number rather than the name.
"""

# fmt: off
FIRST_NAMES = {
    "US": [
        "James", "Mary", "Robert", "Jennifer", "Michael", "Linda", "David",
        "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph",
        "Jessica", "Thomas", "Karen", "Daniel", "Nancy", "Matthew", "Lisa",
    ],
    "IN": [
        "Aarav", "Diya", "Vihaan", "Ananya", "Arjun", "Ishita", "Rohan",
        "Priya", "Kabir", "Meera", "Aditya", "Nisha", "Rahul", "Kavya",
        "Siddharth", "Pooja", "Varun", "Sneha", "Karthik", "Divya",
    ],
    "GB": [
        "Oliver", "Amelia", "Harry", "Isla", "George", "Ava", "Noah",
        "Emily", "Jack", "Sophie", "Charlie", "Grace", "Thomas", "Freya",
        "Oscar", "Poppy", "Alfie", "Chloe", "Henry", "Daisy",
    ],
    "DE": [
        "Lukas", "Hannah", "Felix", "Lena", "Jonas", "Mia", "Leon",
        "Emma", "Paul", "Sophia", "Max", "Marie", "Elias", "Lea",
        "Niklas", "Laura", "Tim", "Johanna", "Moritz", "Clara",
    ],
    "BR": [
        "Miguel", "Alice", "Arthur", "Sophia", "Gabriel", "Helena", "Pedro",
        "Valentina", "Lucas", "Laura", "Matheus", "Isabella", "Rafael",
        "Manuela", "Bruno", "Julia", "Felipe", "Beatriz", "Thiago", "Larissa",
    ],
    "SG": [
        "Wei Jie", "Hui Min", "Jun Hao", "Xin Yi", "Zhi Hao", "Li Ying",
        "Yong Sheng", "Mei Ling", "Kai Xiang", "Shu Fen", "Raj", "Nurul",
        "Haziq", "Siti", "Daniel", "Rachel", "Marcus", "Germaine", "Aloysius",
        "Charmaine",
    ],
}

LAST_NAMES = {
    "US": [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson",
        "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    ],
    "IN": [
        "Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Gupta",
        "Singh", "Mehta", "Rao", "Desai", "Kulkarni", "Joshi", "Bose",
        "Chatterjee", "Malhotra", "Agarwal", "Pillai", "Banerjee", "Kapoor",
    ],
    "GB": [
        "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson",
        "Davies", "Patel", "Robinson", "Wright", "Thompson", "Evans",
        "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Clarke",
    ],
    "DE": [
        "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer",
        "Wagner", "Becker", "Schulz", "Hoffmann", "Koch", "Richter",
        "Klein", "Wolf", "Neumann", "Schwarz", "Zimmermann", "Braun",
        "Krüger", "Hofmann",
    ],
    "BR": [
        "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira",
        "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro",
        "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes",
        "Vieira", "Barbosa",
    ],
    "SG": [
        "Tan", "Lim", "Lee", "Ng", "Wong", "Chan", "Koh", "Teo", "Ong",
        "Goh", "Chua", "Yeo", "Low", "Toh", "Sim", "Rahman", "Ibrahim",
        "Kumar", "Pillai", "Chong",
    ],
}
# fmt: on
