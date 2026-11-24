import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.database import init_db
from app.seed import seed_database
import tests.test_triage as t_triage
import tests.test_auth as t_auth
import tests.test_doctors as t_doctors
import tests.test_api_endpoints as t_api

def run_all_tests():
    print("=" * 65)
    print(" 🏥 Running RuralCare AI Complete Automated Verification Suite")
    print("=" * 65)
    
    # Initialize DB and seed
    init_db()
    seed_database()

    passed = 0
    failed = 0

    test_modules = [
        ("Triage & Emergency Safety Layer", t_triage, [
            "test_emergency_rule_cardiac_english",
            "test_emergency_rule_snakebite_kannada",
            "test_emergency_rule_respiratory_hindi",
            "test_emergency_rule_stroke_tamil",
            "test_emergency_rule_unresponsive_telugu",
            "test_non_emergency_mild_symptom",
            "test_followup_questions_generation",
            "test_heuristic_triage_evaluation",
        ]),
        ("Authentication & Patient Security", t_auth, [
            "test_password_hashing",
            "test_jwt_token",
            "test_demo_patient_exists"
        ]),
        ("Doctor Finder & Geo Distance", t_doctors, [
            "test_haversine_distance",
            "test_get_doctors_all",
            "test_get_doctors_district_filter",
            "test_get_doctors_emergency_capable",
            "test_get_doctors_distance_sorting"
        ]),
        ("FastAPI Endpoints End-to-End", t_api, [
            "test_health_check",
            "test_homepage_serves_html",
            "test_auth_flow",
            "test_triage_emergency_route",
            "test_triage_non_emergency_and_followup",
            "test_doctors_routes",
            "test_emergency_routes",
            "test_patient_history"
        ])
    ]

    for category, mod, funcs in test_modules:
        print(f"\n[Category] {category}:")
        for fn_name in funcs:
            fn = getattr(mod, fn_name, None)
            if not fn:
                print(f"  ❌ {fn_name}: Function not found!")
                failed += 1
                continue
            try:
                fn()
                print(f"  ✅ {fn_name}: PASSED")
                passed += 1
            except Exception as e:
                print(f"  ❌ {fn_name}: FAILED -> {e}")
                failed += 1

    print("\n" + "=" * 65)
    print(f" Test Results Summary: Total={passed + failed}, Passed={passed}, Failed={failed}")
    print("=" * 65)

    if failed > 0:
        sys.exit(1)
    else:
        print(" 🎉 All 24 RuralCare AI verification tests PASSED with 100% success!")

if __name__ == "__main__":
    run_all_tests()
