import re


class BookingParser:
    def extract(self, query: str, fields: list[str]):
        result = {field: "not provided" for field in fields}
        q = query.lower()

        money = re.search(r"\$\s?\d+|under\s+\$?\d+|below\s+\$?\d+|less than\s+\$?\d+", q)
        if money:
            for key in ["budget", "amount", "price_limit"]:
                if key in result:
                    result[key] = money.group(0)

        people = re.search(r"(\d+)\s+(people|persons|guests|passengers|travelers|tickets|seats)", q)
        if people:
            for key in ["guests", "passengers", "travelers", "tickets", "seats", "party_size"]:
                if key in result:
                    result[key] = people.group(1)

        nights = re.search(r"(\d+)\s+nights?", q)
        if nights and "nights" in result:
            result["nights"] = nights.group(1)

        cities = ["dallas", "frisco", "plano", "new york", "las vegas", "chicago", "austin", "hyderabad", "paris", "london", "texas health frisco"]
        for city in cities:
            if city in q:
                for key in ["city", "location", "destination", "drop", "hospital"]:
                    if key in result and result[key] == "not provided":
                        result[key] = city.title()

        match = re.search(r"from\s+([a-zA-Z ]+?)\s+to\s+([a-zA-Z ]+?)(\s|$|tomorrow|today|next)", q)
        if match:
            if "origin" in result:
                result["origin"] = match.group(1).strip().title()
            if "source" in result:
                result["source"] = match.group(1).strip().title()
            if "destination" in result:
                result["destination"] = match.group(2).strip().title()

        for date_word in ["today", "tomorrow", "tonight"]:
            if date_word in q:
                for key in ["date", "check_in", "dates", "time"]:
                    if key in result:
                        result[key] = date_word

        for word in ["morning", "afternoon", "evening", "night"]:
            if word in q and "time" in result:
                result["time"] = word

        for cuisine in ["italian", "indian", "mexican", "chinese", "thai"]:
            if cuisine in q and "cuisine" in result:
                result["cuisine"] = cuisine.title()

        return result
