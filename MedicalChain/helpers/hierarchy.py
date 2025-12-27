import json
import os


class HierarchyHelper:
    def __init__(self):
        self.hierarchy_path = os.path.join(
            os.path.dirname(__file__),
            "../constants/medicalHierarchy.json",
        )
        self.hierarchy = self._load_hierarchy()
        self.flat_map = self._create_flat_map()

    def _load_hierarchy(self):
        with open(self.hierarchy_path) as f:
            return json.load(f)

    def _create_flat_map(self):
        flat = {
            0: "All Specializations (General Access)",  # Fallback code when classification fails
        }
        for category_id, category_data in self.hierarchy.items():
            specialties = category_data.get("specialties", {})
            for specialty_id, specialty_data in specialties.items():
                codes = specialty_data.get("codes", {})
                for code, name in codes.items():
                    flat[int(code)] = name
        return flat

    def get_name_by_code(self, code: int) -> str:
        return self.flat_map.get(code, "Unknown")

    def get_code_by_name(self, name: str) -> int:
        name_lower = name.lower()
        for code, spec_name in self.flat_map.items():
            if name_lower in spec_name.lower() or spec_name.lower() in name_lower:
                return code
        return None

    def get_all_codes(self):
        return list(self.flat_map.keys())

    def get_all_specializations(self):
        return [{"code": code, "name": name} for code, name in self.flat_map.items()]

    def add_specialization(
        self,
        code: int,
        name: str,
        category_id: str,
        specialty_id: str,
    ):
        try:
            if category_id not in self.hierarchy:
                self.hierarchy[category_id] = {"name": "", "specialties": {}}
            if specialty_id not in self.hierarchy[category_id]["specialties"]:
                self.hierarchy[category_id]["specialties"][specialty_id] = {
                    "name": "",
                    "codes": {},
                }
            self.hierarchy[category_id]["specialties"][specialty_id]["codes"][
                str(code)
            ] = name
            with open(self.hierarchy_path, "w") as f:
                json.dump(self.hierarchy, f, indent=2)
            self.flat_map[code] = name
            return True
        except Exception as e:
            print(f"Error adding specialization: {e}")
            return False


hierarchy_helper = HierarchyHelper()
