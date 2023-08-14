def get_i_frame_min(matrix):
    entries = []
    max_cvs = [-1E30, -1E30]
    for row in matrix:
        for cell in row:
            label = cell.get("label")
            if not label:
                continue
            cvs = parse_cv_from_label(label)
            for i_cv in range(2):
                if cvs[i_cv] > max_cvs[i_cv]:
                    max_cvs[i_cv] = cvs[i_cv]
            if "iFrameTraj" in cell:
                i_frame = cell["iFrameTraj"][0]
                value = cell.get("value")
                if value is None:
                    continue
                entries.append({
                    "i_frame": cell["iFrameTraj"][0],
                    "value": float(cell["value"]),
                    "cv": cvs
                })
    cutoff_cvs = [0.95 * cv for cv in max_cvs]
    for entry in entries:
        for i_cv in range(2):
            if entry["cv"][i_cv] > cutoff_cvs[i_cv]:
                entry["value"] = 0.
    entries.sort(key=lambda e: e["value"])
    return entries[0]["i_frame"]


def parse_cv_from_label(label):
    label = label.split("=")[1].replace("fe", "")
    pieces = label.split(",")
    return [float(p) for p in pieces]
