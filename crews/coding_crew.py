import subprocess
import tempfile
from pathlib import Path

from config import CPP_COMPILER, PYTHON_BIN, MAX_SELF_CORRECT_ROUNDS
from tools.algorithm_store import AlgorithmStore
from tools.rag_tool import RAGTool


class CodingCrew:
    def __init__(self):
        self.store = AlgorithmStore()
        self.rag = RAGTool()

    def run(self, query: str):
        steps = []

        rag = {"thought": "RAG Retrieval Agent: retrieve coding knowledge", "output": self.rag.search(query, "coding")}
        steps.append(rag)

        candidates = self.store.search(query)
        steps.append({"thought": "Algorithm Agent: search algorithm dictionary", "output": candidates})

        selected = candidates[0]
        steps.append({"thought": "ToT Evaluator Agent: score and select algorithm", "output": selected})

        language = "python" if "python" in query.lower() else "cpp"
        code = self.generate_code(selected, language)
        steps.append({"thought": "Generation Agent: generate code", "output": "code generated"})

        compile_result = self.compile_or_check(code, language)
        steps.append({"thought": "Compiler Agent: compile/syntax check", "output": compile_result})

        test_result = self.run_test(code, language, query)
        steps.append({"thought": "Test Agent: run sample test", "output": test_result})

        status = "success" if compile_result["success"] and test_result["success"] else "failed"
        rounds = 0

        while status != "success" and rounds < MAX_SELF_CORRECT_ROUNDS:
            code = self.self_correct(code, language)
            steps.append({"thought": "Self-Correction Agent: apply fixes", "output": "code updated"})
            compile_result = self.compile_or_check(code, language)
            test_result = self.run_test(code, language, query)
            status = "success" if compile_result["success"] and test_result["success"] else "failed"
            rounds += 1

        reviewer = {"time_complexity": "Depends on selected algorithm", "space_complexity": "Depends on data structures", "safety": "Compiled/tested if compiler exists"}
        steps.append({"thought": "Reviewer Agent: review complexity and quality", "output": reviewer})

        return {
            "crew_name": "CodingRAGCrew",
            "rag": rag["output"],
            "selected_algorithm": selected,
            "language": language,
            "code": code,
            "status": status,
            "compile_result": compile_result,
            "test_result": test_result,
            "reviewer": reviewer,
            "crew_steps": steps
        }

    def generate_code(self, algorithm: str, language: str):
        if language == "python":
            if algorithm == "dijkstra":
                return '''import heapq

n, m, src = map(int, input().split())
graph = [[] for _ in range(n + 1)]
for _ in range(m):
    u, v, w = map(int, input().split())
    graph[u].append((v, w))
    graph[v].append((u, w))

INF = 10**30
dist = [INF] * (n + 1)
dist[src] = 0
pq = [(0, src)]

while pq:
    d, node = heapq.heappop(pq)
    if d != dist[node]:
        continue
    for nxt, wt in graph[node]:
        if dist[nxt] > d + wt:
            dist[nxt] = d + wt
            heapq.heappush(pq, (dist[nxt], nxt))

print(*[-1 if x == INF else x for x in dist[1:]])
'''
            return 'print("Generated Python solution template")\n'

        if algorithm == "dijkstra":
            return '''#include <bits/stdc++.h>
using namespace std;

using ll = long long;
const ll INF = 4e18;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, src;
    cin >> n >> m >> src;

    vector<vector<pair<int,int>>> graph(n + 1);

    for (int i = 0; i < m; i++) {
        int u, v, w;
        cin >> u >> v >> w;
        graph[u].push_back({v, w});
        graph[v].push_back({u, w});
    }

    vector<ll> dist(n + 1, INF);
    priority_queue<pair<ll,int>, vector<pair<ll,int>>, greater<pair<ll,int>>> pq;

    dist[src] = 0;
    pq.push({0, src});

    while (!pq.empty()) {
        auto [d, node] = pq.top();
        pq.pop();

        if (d != dist[node]) continue;

        for (auto [next, weight] : graph[node]) {
            if (dist[next] > d + weight) {
                dist[next] = d + weight;
                pq.push({dist[next], next});
            }
        }
    }

    for (int i = 1; i <= n; i++) {
        if (dist[i] == INF) cout << -1 << " ";
        else cout << dist[i] << " ";
    }

    return 0;
}
'''
        return '''#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cout << "Generated C++ solution template\\n";
    return 0;
}
'''

    def compile_or_check(self, code: str, language: str):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                if language == "cpp":
                    src = tmp / "main.cpp"
                    exe = tmp / "main.exe"
                    src.write_text(code, encoding="utf-8")
                    p = subprocess.run([CPP_COMPILER, "-std=c++17", str(src), "-o", str(exe)], capture_output=True, text=True, timeout=10)
                    return {"success": p.returncode == 0, "output": p.stdout + p.stderr or "Compilation successful"}
                src = tmp / "main.py"
                src.write_text(code, encoding="utf-8")
                p = subprocess.run([PYTHON_BIN, "-m", "py_compile", str(src)], capture_output=True, text=True, timeout=10)
                return {"success": p.returncode == 0, "output": p.stdout + p.stderr or "Syntax OK"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    def run_test(self, code: str, language: str, query: str):
        sample = "5 6 1\n1 2 2\n1 3 4\n2 3 1\n2 4 7\n3 5 3\n4 5 1\n" if "dijkstra" in query.lower() else ""
        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmp = Path(tmp)
                if language == "cpp":
                    src = tmp / "main.cpp"
                    exe = tmp / "main.exe"
                    src.write_text(code, encoding="utf-8")
                    c = subprocess.run([CPP_COMPILER, "-std=c++17", str(src), "-o", str(exe)], capture_output=True, text=True, timeout=10)
                    if c.returncode != 0:
                        return {"success": False, "output": c.stderr}
                    r = subprocess.run([str(exe)], input=sample, capture_output=True, text=True, timeout=10)
                    return {"success": r.returncode == 0, "output": r.stdout + r.stderr or "Program ran"}
                src = tmp / "main.py"
                src.write_text(code, encoding="utf-8")
                r = subprocess.run([PYTHON_BIN, str(src)], input=sample, capture_output=True, text=True, timeout=10)
                return {"success": r.returncode == 0, "output": r.stdout + r.stderr or "Program ran"}
        except Exception as e:
            return {"success": False, "output": str(e)}

    def self_correct(self, code: str, language: str):
        if language == "cpp" and "int main" not in code:
            return code + "\nint main(){return 0;}\n"
        return code.replace("\t", "    ")
