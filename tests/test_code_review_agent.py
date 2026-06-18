from agents.agent_router import AgentRouter
from agents.code_review_agent import CodeReviewAgent


def test_cpp_tle_review_without_code_asks_for_code():
    result = CodeReviewAgent().run("My C++ code gives TLE. Find bottleneck.")
    crew = result["extra"]["crew_result"]

    assert result["agent"] == "CodeReviewAgent"
    assert crew["status"] == "need_code"
    assert crew["language"] == "cpp"
    assert crew["code_quality_score"] is None
    assert result["answer"] == "Please paste your C++ code so I can find the TLE bottleneck and optimize it."
    assert "0/100" not in result["answer"]
    assert "Language: python" not in result["answer"]


def test_router_sends_cpp_tle_bottleneck_to_code_review():
    route, agent = AgentRouter().route("My C++ code gives TLE. Find bottleneck.")

    assert route == "code_review"
    assert agent.name == "CodeReviewAgent"


def test_cpp_tle_review_with_code_runs_review():
    code = """
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<int> a(n);
    for (int i = 0; i < n; i++) cin >> a[i];
    long long ans = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (a[i] < a[j]) ans++;
        }
    }
    cout << ans << "\\n";
}
"""

    result = CodeReviewAgent().run("My C++ code gives TLE. Find bottleneck.", code=code)
    crew = result["extra"]["crew_result"]

    assert crew.get("status") != "need_code"
    assert crew["language"] == "cpp"
    assert crew["code_quality_score"]["overall"] >= 0
    assert "O(n" in crew["time_complexity"]
    assert "higher" not in crew["time_complexity"]
    assert "Code Quality Score" in result["answer"]
    assert "Reviewed Code" in result["answer"]
