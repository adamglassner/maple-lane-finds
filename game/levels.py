"""Chapter, scene and object data for Maple Lane Finds."""

OBJECT_NAMES = {
    "pumpkin": "Pumpkin", "jackolantern": "Jack-o'-Lantern", "apple": "Apple", "pear": "Pear",
    "acorn": "Acorn", "maple_leaf": "Maple Leaf", "oak_leaf": "Oak Leaf", "corn": "Ear of Corn",
    "candy_corn": "Candy Corn", "wrapped_candy": "Wrapped Candy", "lollipop": "Lollipop",
    "candy_bucket": "Candy Bucket", "straw_hat": "Straw Hat", "scarf": "Scarf", "pie": "Pie",
    "cupcake": "Cupcake", "cookie": "Cookie", "cider_mug": "Cider Mug", "rolling_pin": "Rolling Pin",
    "sunflower": "Sunflower", "watering_can": "Watering Can", "mushroom": "Mushroom", "basket": "Basket",
    "lantern": "Lantern", "teapot": "Teapot", "ribbon": "Ribbon Bow", "honey_jar": "Honey Jar",
    "pinecone": "Pinecone", "fox_mask": "Fox Mask", "bluebird": "Bluebird", "mitten": "Mitten",
    "gourd": "Gourd", "horseshoe": "Horseshoe", "rubber_boot": "Rain Boot", "kite": "Kite",
    "birdhouse": "Birdhouse", "caramel_apple": "Caramel Apple", "balloon": "Balloon", "ticket": "Fair Ticket",
    "teddy_bear": "Teddy Bear",
}
ALL_OBJECTS = list(OBJECT_NAMES)

# Each scene's background art already contains some decorations (pumpkins in the patch, corn in the barn...).
# Find-list items never repeat a decoration in the same scene, so players are never tricked.
CHAPTERS = [
    {
        "n": 1, "title": "Pumpkin Patch", "scene": "pumpkin_patch",
        "intro": "The patch is full of pumpkins. Can you find the other harvest goodies?",
        "targets": ["jackolantern", "acorn", "maple_leaf", "watering_can", "rubber_boot", "bluebird",
                    "sunflower", "gourd", "candy_bucket", "apple"],
        "avoid": ["pumpkin", "straw_hat"],
        "puzzle": "memory", "puzzle_title": "Pumpkin Pairs",
    },
    {
        "n": 2, "title": "Harvest Barn", "scene": "harvest_barn",
        "intro": "Sunlight is pouring into the old barn. Let's tidy up!",
        "targets": ["horseshoe", "lantern", "basket", "wrapped_candy", "pinecone", "mitten", "scarf",
                    "honey_jar", "apple", "birdhouse"],
        "avoid": ["pumpkin", "gourd", "corn"],
        "puzzle": "spot", "puzzle_title": "Barn Differences",
    },
    {
        "n": 3, "title": "Autumn Bakery", "scene": "autumn_bakery",
        "intro": "Something smells delicious! The bakery is getting ready for the fair.",
        "targets": ["pie", "cupcake", "cookie", "rolling_pin", "teapot", "cider_mug", "pear",
                    "candy_corn", "wrapped_candy", "oak_leaf"],
        "avoid": ["pumpkin", "basket", "apple", "honey_jar"],
        "puzzle": "slider", "puzzle_title": "Pie Picture Slide",
    },
    {
        "n": 4, "title": "Corn Maze Garden", "scene": "corn_maze",
        "intro": "Tall corn, bright flowers, and a few things folks dropped along the path.",
        "targets": ["pumpkin", "mushroom", "fox_mask", "kite", "ribbon", "watering_can", "pinecone",
                    "oak_leaf", "teddy_bear", "straw_hat"],
        "avoid": ["gourd"],
        "puzzle": "maze", "puzzle_title": "Corn Maze Path",
    },
    {
        "n": 5, "title": "Fall Fair Market", "scene": "fall_fair",
        "intro": "The harvest fair is here! Find everything for the big celebration.",
        "targets": ["caramel_apple", "balloon", "ticket", "lollipop", "teddy_bear", "honey_jar", "gourd",
                    "candy_corn", "apple", "ribbon"],
        "avoid": ["pumpkin", "corn", "pie", "cupcake", "cookie", "sunflower", "maple_leaf", "basket"],
        "puzzle": "pattern", "puzzle_title": "Harvest Code",
    },
]


ZONES = {
    "pumpkin_patch": {"tint": (240, 232, 218), "zones": [
        (60, 610, 1860, 835, 6), (60, 470, 1100, 600, 2), (1300, 470, 1860, 600, 1)]},
    "harvest_barn": {"tint": (232, 214, 198), "zones": [
        (60, 380, 1090, 740, 4), (60, 745, 1880, 835, 4), (60, 230, 780, 320, 2), (1680, 600, 1900, 690, 1),
        (1190, 620, 1610, 835, 1)]},
    "autumn_bakery": {"tint": (244, 234, 220), "zones": [
        (500, 560, 1890, 655, 5), (100, 220, 510, 295, 2), (100, 400, 510, 475, 2), (1410, 220, 1830, 295, 2),
        (1410, 400, 1830, 475, 2), (740, 460, 1180, 535, 1), (70, 520, 460, 600, 1), (510, 720, 1890, 835, 2)]},
    "corn_maze": {"tint": (240, 232, 214), "zones": [
        (330, 540, 1630, 835, 5), (60, 430, 800, 835, 3), (1110, 430, 1880, 835, 3)]},
    "fall_fair": {"tint": (242, 232, 220), "zones": [
        (60, 720, 1880, 835, 4), (70, 600, 470, 690, 2), (995, 560, 1370, 650, 2), (1465, 580, 1860, 670, 2),
        (620, 640, 1160, 835, 2), (560, 520, 960, 700, 1)]},
}


def chapter(n):
    return CHAPTERS[n - 1]


# Difficulty tuning (sizes are in 1920x1080 game pixels)
DIFFICULTY = {
    "relaxed": {"label": "Relaxed", "size": 128, "clutter": 9, "hint_cooldown": 8, "timer": False,
                "time_goal": None, "wrong_penalty": 0,
                "desc": "No timer, quick hints, and no penalties. Just relax and enjoy."},
    "normal": {"label": "Normal", "size": 108, "clutter": 16, "hint_cooldown": 20, "timer": True,
               "time_goal": 300, "wrong_penalty": 0,
               "desc": "A gentle timer for bonus stars and a little more to search through."},
    "challenge": {"label": "Challenge", "size": 88, "clutter": 24, "hint_cooldown": 40, "timer": True,
                  "time_goal": 180, "wrong_penalty": 3,
                  "desc": "Smaller items, more clutter, slower hints. Random clicking adds 3 seconds."},
}


def stars_for(hints_used, seconds, difficulty):
    stars = 3
    if hints_used >= 3:
        stars -= 2
    elif hints_used >= 1:
        stars -= 1
    goal = DIFFICULTY[difficulty]["time_goal"]
    if goal and seconds > goal:
        stars -= 1
    return max(1, stars)
