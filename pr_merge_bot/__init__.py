"""PR Merge Bot - Automated PR merge with smart criteria."""
import urllib.request, json, time

class PRMergeBot:
    def __init__(self, token, owner="Raphasha27", repo="repopulse"):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.headers = {"Authorization": "token " + token, "Accept": "application/vnd.github+json"}
        self.hput = {**self.headers, "Content-Type": "application/json"}

    def get_open_prs(self):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls?state=open"
        return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=self.headers)).read())

    def can_merge(self, pr):
        if pr.get("mergeable") != True:
            return False, "not mergeable"
        labels = [l["name"] for l in pr.get("labels", [])]
        if "do-not-merge" in labels:
            return False, "blocked by label"
        if pr["mergeable_state"] == "dirty":
            return False, "merge conflicts"
        return True, "ready"

    def merge(self, pr, method="squash"):
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls/{pr['number']}/merge"
        data = json.dumps({"merge_method": method, "commit_title": pr["title"]}).encode()
        req = urllib.request.Request(url, data=data, headers=self.hput, method="PUT")
        try:
            resp = urllib.request.urlopen(req)
            return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return {"error": e.code, "message": e.read().decode()[:200]}

    def run(self):
        prs = self.get_open_prs()
        results = []
        for pr in prs:
            ok, reason = self.can_merge(pr)
            if ok:
                result = self.merge(pr)
                results.append({"number": pr["number"], "title": pr["title"], "merged": True, "result": result})
            else:
                results.append({"number": pr["number"], "title": pr["title"], "merged": False, "reason": reason})
            time.sleep(1)
        return results

if __name__ == "__main__":
    import sys
    token = sys.argv[1] if len(sys.argv) > 1 else ""
    if token:
        bot = PRMergeBot(token)
        print(json.dumps(bot.run(), indent=2))
