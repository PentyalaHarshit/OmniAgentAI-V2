from agents.agent_router import AgentRouter
from agents.cab_agent import CabAgent
from agents.event_agent import EventAgent
from agents.fitness_agent import FitnessAgent
from agents.hotel_agent import HotelAgent
from agents.local_discovery_agent import LocalDiscoveryAgent
from agents.recipe_agent import RecipeAgent
from agents.restaurant_agent import RestaurantAgent
from agents.vacation_package_agent import VacationPackageAgent


def test_hotel_booking_agent_output():
    result = HotelAgent().run("Book a hotel in New York for 3 nights under $200 per night.")

    assert "HotelBookingAgent / hotel" in result["answer"]
    assert "Top Hotels" in result["answer"]
    assert "Marriott Times Square" in result["answer"]
    assert "$180/night" in result["answer"]
    assert "Book now?" in result["answer"]


def test_restaurant_agent_output():
    result = RestaurantAgent().run("Find Indian restaurants near me.")

    assert "RestaurantAgent / restaurant" in result["answer"]
    assert "Spice Grill" in result["answer"]
    assert "Available Table" in result["answer"]
    assert "Reserve table?" in result["answer"]


def test_event_ride_vacation_outputs():
    event = EventAgent().run("Find concerts in Dallas this weekend.")
    assert "EventBookingAgent / event" in event["answer"]
    assert "Dallas Summer Beats" in event["answer"]

    ride = CabAgent().run("Book a ride from Plano to DFW Airport.")
    assert "RideBookingAgent / cab" in ride["answer"]
    assert "Pickup: Plano" in ride["answer"]
    assert "Destination: DFW Airport" in ride["answer"]

    vacation = VacationPackageAgent().run("Plan a 5-day vacation to Japan.")
    assert "VacationPlannerAgent / vacation_package" in vacation["answer"]
    assert "Day 3:" in vacation["answer"]
    assert "Mt. Fuji" in vacation["answer"]


def test_fitness_recipe_local_outputs():
    fitness = FitnessAgent().run("Create a workout plan for muscle gain.")
    assert "Workout Plan for Muscle Gain" in fitness["answer"]
    assert "Day 1: Chest" in fitness["answer"]

    recipe = RecipeAgent().run("Suggest high-protein vegetarian meals.")
    assert "Breakfast:" in recipe["answer"]
    assert "Paneer Omelette" in recipe["answer"]

    local = LocalDiscoveryAgent().run("What are the top tourist attractions in Dallas?")
    assert "Top Places" in local["answer"]
    assert "Dallas Arboretum" in local["answer"]


def test_router_new_booking_lifestyle_routes():
    router = AgentRouter()
    cases = {
        "Book a hotel in New York for 3 nights under $200 per night.": "hotel",
        "Find Indian restaurants near me.": "restaurant",
        "Find concerts in Dallas this weekend.": "event",
        "Book a ride from Plano to DFW Airport.": "cab",
        "Plan a 5-day vacation to Japan.": "vacation_package",
        "Create a workout plan for muscle gain.": "fitness",
        "Suggest high-protein vegetarian meals.": "recipe",
        "What are the top tourist attractions in Dallas?": "local_discovery",
    }
    for query, expected in cases.items():
        route, _ = router.route(query)
        assert route == expected
