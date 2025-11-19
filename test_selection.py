from domain_detector import DomainDetector

d = DomainDetector()

# Test with a marketing objective
objective = "Create a marketing campaign for new product"
scores = d.score_all_domains(objective)

print(f"Objective: {objective}")
print("All scores (sorted by score):")
for domain, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
    print(f"  {domain}: {score:.3f}")

selected = d.detect(objective)
print(f"\nSelected domain: {selected}")
print(f"Selected score: {scores[selected]:.3f}")

# Test with a more ambiguous objective
print("\n" + "="*50)
objective2 = "Build a system to track user engagement"
scores2 = d.score_all_domains(objective2)

print(f"Objective: {objective2}")
print("All scores (sorted by score):")
for domain, score in sorted(scores2.items(), key=lambda x: x[1], reverse=True):
    print(f"  {domain}: {score:.3f}")

selected2 = d.detect(objective2)
print(f"\nSelected domain: {selected2}")
print(f"Selected score: {scores2[selected2]:.3f}")

