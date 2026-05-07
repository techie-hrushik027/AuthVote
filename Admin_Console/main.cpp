#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <cstdlib>

using namespace std;

class Candidate
{
public:
    string name;
    int vote_count;
    Candidate(string n, int v) : name(n), vote_count(v) {}
};

class ElectionEngine
{
private:
    vector<Candidate> liveResults;
    void quickSort(int low, int high)
    {
        if (low >= high)
            return;
        int pivot = liveResults[high].vote_count, i = low - 1;
        for (int j = low; j < high; j++)
        {
            if (liveResults[j].vote_count > pivot)
                swap(liveResults[++i], liveResults[j]);
        }
        swap(liveResults[i + 1], liveResults[high]);
        quickSort(low, i);
        quickSort(i + 2, high);
    }

public:
    void processResults()
    {
        liveResults.clear();
        ifstream file("C:\\Users\\user\\Desktop\\Auth-Vote\\Admin_Console\\live_results.txt");
        if (!file.is_open())
        {
            cerr << "[!] No data. End Election first." << endl;
            return;
        }
        string line, n, v;
        while (getline(file, line))
        {
            stringstream ss(line);
            getline(ss, n, ',');
            getline(ss, v, ',');
            liveResults.push_back(Candidate(n, stoi(v)));
        }

        quickSort(0, liveResults.size() - 1);
        cout << "\n========== FINAL LEADERBOARD ==========" << endl;
        for (size_t i = 0; i < liveResults.size(); i++)
            cout << (i + 1) << ". " << liveResults[i].name << " - " << liveResults[i].vote_count << " Votes\n";
        cout << "=======================================\n";
    }
};

int main()
{
    ElectionEngine engine;
    string pyExe = "C:\\Users\\user\\.pyenv\\pyenv-win\\versions\\3.12.8\\python.exe ";
    string scriptPath = "C:\\Users\\user\\Desktop\\Auth-Vote\\Backend\\admin_tools.py ";
    string pyCommand = pyExe + scriptPath;
    string serverCmd = "start cmd /k \"cd /d C:\\Users\\user\\Desktop\\Auth-Vote\\Backend && " + pyExe + "-m uvicorn app:app --reload --port 8000\"";

    while (true)
    {
        cout << "  AUTHVOTE - MASTER ADMIN CONSOLE " << endl;
        cout << "[1] START ELECTION (Launch Server & Open Polls)" << endl;
        cout << "[2] END ELECTION (Close Polls & Run DAA Quicksort)" << endl;
        cout << "[3] ENTER SINGLE VOTER (Interactive)" << endl;
        cout << "[4] ENTER CANDIDATES (Interactive)" << endl;
        cout << "[5] DELETE ALL VOTERS (Reset Election)" << endl;
        cout << "[6] DELETE ALL CANDIDATES" << endl;
        cout << "[7] DISPATCH AUTOMATED EMAILS (Generate PINs)" << endl;
        cout << "[8] EXIT TERMINAL" << endl;
        cout << "[9] VIEW LIVE DASHBOARD (Open Monitor)" << endl;
        cout << "Select Action: ";

        int choice;
        cin >> choice;

        if (choice == 1)
        {  //python admin_tools.py (pyCommand) start
            system((pyCommand + "start").c_str());
            cout << "[SYSTEM] Spawning FastAPI Server in background...\n";
            system(serverCmd.c_str());
        }
        else if (choice == 2)
        {
            system((pyCommand + "end").c_str());
            engine.processResults();
            cout << "[SYSTEM] Opening Dashboard...\n";
            system("start http://127.0.0.1:8000/dashboard.html");
        }
        else if (choice == 3)
            system((pyCommand + "add_voter").c_str());
        else if (choice == 4)
            system((pyCommand + "add_candidates").c_str());
        else if (choice == 5)
            system((pyCommand + "reset_voters").c_str());
        else if (choice == 6)
            system((pyCommand + "reset_candidates").c_str());
        else if (choice == 7)
            system((pyCommand + "email").c_str());
        else if (choice == 8)
        {
            cout << "Shutting down..." << endl;
            break;
        }
        else if (choice == 9)
            system("start http://127.0.0.1:8000/dashboard.html");
        else
            cout << "Invalid Selection." << endl;
    }
    return 0;
}