[
  {
    "a_id": "A-1",
    "s_refs": ["S-1"],
    "kpi_table": [{"metric":"Uptime","target":99.9,"unit":"%","by_day":30}],
    "falsifications": ["If baseline uptime < 95% last 7 days, target invalid"],
    "risks": ["TLS renewal failures"]
  }
]
