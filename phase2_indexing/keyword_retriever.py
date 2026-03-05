import json
import os
import re

class KeywordRetriever:
    def __init__(self, data_path):
        self.data_path = data_path
        self.data = []
        if os.path.exists(data_path):
            with open(data_path, 'r') as f:
                self.data = json.load(f)
        
    def search(self, query, top_k=3):
        query = query.lower()
        results = []
        
        # Simple keyword matching
        for scheme in self.data:
            scheme_name = scheme.get('scheme_name', '').lower()
            
            # Calculate match score based on how well the query matches the scheme
            match_score = 0
            
            # Exact scheme name match gets highest score
            if scheme_name in query:
                match_score = 1.0
            else:
                # Check for word matches
                scheme_words = [w for w in scheme_name.split() if len(w) > 2]  # Ignore short words
                matched_words = [w for w in scheme_words if w in query]
                if matched_words:
                    match_score = len(matched_words) / len(scheme_words) * 0.8
            
            # If query mentions the scheme
            if match_score > 0:
                # Check for specific attributes in query
                attributes = {
                    "nav": ["nav", "net asset value"],
                    "aum": ["aum", "assets under management", "fund size"],
                    "expense_ratio": ["expense ratio", "fees", "cost"],
                    "exit_load": ["exit load", "exit fee"],
                    "min_sip": ["sip", "minimum sip"],
                    "min_lumpsum": ["lumpsum", "minimum investment"],
                    "lock_in": ["lock in", "lockin"],
                    "risk": ["risk", "riskometer"],
                    "benchmark": ["benchmark", "index"],
                    "turnover": ["turnover"],
                    "return_1y": ["1 year return", "1y return", "return 1 year", "1 year"],
                    "return_3y": ["3 year return", "3y return", "return 3 year", "3 year"],
                    "return_5y": ["5 year return", "5y return", "return 5 year", "5 year"]
                }
                
                found_attr = False
                
                # Special handling for general return queries (show all periods)
                if any(kw in query for kw in ["return", "returns", "performance"]):
                    r1y = scheme.get('return_1y')
                    r3y = scheme.get('return_3y')
                    r5y = scheme.get('return_5y')
                    if r1y or r3y or r5y:
                        content = f"{scheme['scheme_name']} has generated returns of {r1y or 'N/A'} in 1 year, {r3y or 'N/A'} in 3 years, and {r5y or 'N/A'} in 5 years."
                        results.append({
                            "text": content,
                            "source": scheme.get('url'),
                            "scheme": scheme['scheme_name'],
                            "score": match_score
                        })
                        found_attr = True
                
                # Check for specific attributes
                if not found_attr:
                    for attr, keywords in attributes.items():
                        if any(kw in query for kw in keywords):
                            val = scheme.get(attr)
                            if val and val != "N/A":
                                # Format return attributes nicely
                                if attr == "return_1y":
                                    content = f"The 1 year return of {scheme['scheme_name']} is {val}."
                                elif attr == "return_3y":
                                    content = f"The 3 year return of {scheme['scheme_name']} is {val}."
                                elif attr == "return_5y":
                                    content = f"The 5 year return of {scheme['scheme_name']} is {val}."
                                elif attr == "nav":
                                    content = f"The NAV of {scheme['scheme_name']} today is {val}. NAV or Net Asset Value is the per unit price of a mutual fund. For example, if the NAV of a fund is ₹10, it means you can get 1000 units of that mutual fund at ₹10,000."
                                else:
                                    attr_name = attr.replace('_', ' ')
                                    content = f"The {attr_name} of {scheme['scheme_name']} is {val}."
                                results.append({
                                    "text": content,
                                    "source": scheme.get('url'),
                                    "scheme": scheme['scheme_name'],
                                    "score": match_score
                                })
                                found_attr = True
                                break
                
                # If no specific attribute mentioned but scheme name is, provide a summary
                if not found_attr:
                    summary = f"{scheme['scheme_name']}: NAV {scheme.get('nav')}, Expense Ratio {scheme.get('expense_ratio')}, Risk: {scheme.get('risk')}."
                    results.append({
                        "text": summary,
                        "source": scheme.get('url'),
                        "scheme": scheme['scheme_name'],
                        "score": match_score * 0.8
                    })

        # Sort by score and limit
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        return results[:top_k]
