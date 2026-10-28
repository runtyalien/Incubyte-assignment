"""Name pools per country, so the Bangalore office doesn't read as Ohio.

Sized so that sorting 10,000 people by name does not produce a screen of
identical rows. Thirty-six by thirty-six is about 1,300 combinations per
country, which leaves the occasional shared name — as any real organisation
has — without the directory looking broken. Uniqueness is carried by the staff
number, not the name.
"""

# fmt: off
FIRST_NAMES = {
    "US": [
        "James", "Mary", "Robert", "Jennifer", "Michael", "Linda", "David",
        "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph",
        "Jessica", "Thomas", "Karen", "Daniel", "Nancy", "Matthew", "Lisa",
        "Anthony", "Margaret", "Mark", "Sandra", "Steven", "Ashley", "Paul",
        "Emily", "Andrew", "Donna", "Joshua", "Michelle", "Kevin", "Carol",
        "Brian", "Amanda",
    ],
    "IN": [
        "Aarav", "Diya", "Vihaan", "Ananya", "Arjun", "Ishita", "Rohan",
        "Priya", "Kabir", "Meera", "Aditya", "Nisha", "Rahul", "Kavya",
        "Siddharth", "Pooja", "Varun", "Sneha", "Karthik", "Divya",
        "Anirudh", "Shreya", "Nikhil", "Aditi", "Harsh", "Tanvi", "Manish",
        "Riya", "Vikram", "Lakshmi", "Sanjay", "Neha", "Gaurav", "Swati",
        "Abhishek", "Deepa",
    ],
    "GB": [
        "Oliver", "Amelia", "Harry", "Isla", "George", "Ava", "Noah",
        "Emily", "Jack", "Sophie", "Charlie", "Grace", "Thomas", "Freya",
        "Oscar", "Poppy", "Alfie", "Chloe", "Henry", "Daisy",
        "Arthur", "Ruby", "Leo", "Evie", "Archie", "Phoebe", "Theo",
        "Matilda", "Freddie", "Imogen", "Jacob", "Rosie", "Edward", "Holly",
        "Samuel", "Eleanor",
    ],
    "DE": [
        "Lukas", "Hannah", "Felix", "Lena", "Jonas", "Mia", "Leon",
        "Emma", "Paul", "Sophia", "Max", "Marie", "Elias", "Lea",
        "Niklas", "Laura", "Tim", "Johanna", "Moritz", "Clara",
        "Jan", "Anna", "Philipp", "Julia", "Fabian", "Nina", "Sebastian",
        "Katharina", "Tobias", "Lisa", "Florian", "Sarah", "Daniel", "Helena",
        "Simon", "Franziska",
    ],
    "BR": [
        "Miguel", "Alice", "Arthur", "Sophia", "Gabriel", "Helena", "Pedro",
        "Valentina", "Lucas", "Laura", "Matheus", "Isabella", "Rafael",
        "Manuela", "Bruno", "Julia", "Felipe", "Beatriz", "Thiago", "Larissa",
        "Gustavo", "Camila", "Leonardo", "Mariana", "Eduardo", "Fernanda",
        "Caio", "Gabriela", "Vinicius", "Amanda", "Rodrigo", "Carolina",
        "Diego", "Patricia", "Andre", "Juliana",
    ],
    "SG": [
        "Wei Jie", "Hui Min", "Jun Hao", "Xin Yi", "Zhi Hao", "Li Ying",
        "Yong Sheng", "Mei Ling", "Kai Xiang", "Shu Fen", "Raj", "Nurul",
        "Haziq", "Siti", "Daniel", "Rachel", "Marcus", "Germaine", "Aloysius",
        "Charmaine", "Jia Hui", "Wen Xuan", "Yi Ting", "Cheng Yu", "Hui Shan",
        "Ming Hao", "Priya", "Farah", "Amirul", "Sharifah", "Benjamin",
        "Clarissa", "Jonathan", "Natasha", "Ryan", "Valerie",
    ],
}

LAST_NAMES = {
    "US": [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
        "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson",
        "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
        "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez",
        "Lewis", "Robinson", "Walker", "Young", "Allen", "King", "Wright",
        "Scott", "Torres",
    ],
    "IN": [
        "Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Gupta",
        "Singh", "Mehta", "Rao", "Desai", "Kulkarni", "Joshi", "Bose",
        "Chatterjee", "Malhotra", "Agarwal", "Pillai", "Banerjee", "Kapoor",
        "Chopra", "Saxena", "Trivedi", "Menon", "Shetty", "Bhat", "Deshpande",
        "Mukherjee", "Ghosh", "Sinha", "Bhatia", "Chauhan", "Tiwari",
        "Mishra", "Dutta", "Kaur",
    ],
    "GB": [
        "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson",
        "Davies", "Patel", "Robinson", "Wright", "Thompson", "Evans",
        "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Clarke",
        "Jackson", "Hughes", "Edwards", "Turner", "Harris", "Cooper",
        "Morgan", "King", "Baker", "Hill", "Ward", "Watson", "Bennett",
        "Shaw", "Ellis", "Murray",
    ],
    "DE": [
        "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer",
        "Wagner", "Becker", "Schulz", "Hoffmann", "Koch", "Richter",
        "Klein", "Wolf", "Neumann", "Schwarz", "Zimmermann", "Braun",
        "Krüger", "Hofmann", "Hartmann", "Lange", "Schmitt", "Werner",
        "Krause", "Meier", "Lehmann", "Schmid", "Schulze", "Maier", "Köhler",
        "Herrmann", "Walter", "König", "Mayer", "Huber",
    ],
    "BR": [
        "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira",
        "Alves", "Pereira", "Lima", "Gomes", "Costa", "Ribeiro",
        "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes",
        "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade",
        "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas",
        "Cardoso", "Ramos", "Gonçalves", "Santana", "Teixeira", "Correia",
    ],
    "SG": [
        "Tan", "Lim", "Lee", "Ng", "Wong", "Chan", "Koh", "Teo", "Ong",
        "Goh", "Chua", "Yeo", "Low", "Toh", "Sim", "Rahman", "Ibrahim",
        "Kumar", "Pillai", "Chong", "Chew", "Loh", "Seah", "Tay", "Quek",
        "Foo", "Heng", "Soh", "Yap", "Phua", "Hassan", "Osman", "Devi",
        "Raman", "Khoo", "Leong",
    ],
}
# fmt: on
