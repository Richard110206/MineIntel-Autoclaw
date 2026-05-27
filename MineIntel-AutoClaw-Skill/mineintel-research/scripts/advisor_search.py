#!/usr/bin/env python3
"""Search official university/college pages for advisor candidates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import web_search  # noqa: E402

try:
    import open_link  # noqa: E402
except Exception:  # pragma: no cover - optional AutoGLM capability
    open_link = None  # type: ignore[assignment]


DEFAULT_DOMAINS = (
    "www.cumt.edu.cn",
    "faculty.cumt.edu.cn",
    "cese.cumt.edu.cn",
    "safe.cumt.edu.cn",
    "cace.cumt.edu.cn",
    "cmee.cumt.edu.cn",
    "siee.cumt.edu.cn",
    "sres.cumt.edu.cn",
    "scet.cumt.edu.cn",
    "cesi.cumt.edu.cn",
    "see.cumt.edu.cn",
    "slepe.cumt.edu.cn",
    "smsp.cumt.edu.cn",
    "math.cumt.edu.cn",
    "cs.cumt.edu.cn",
    "sm.cumt.edu.cn",
    "cllp.cumt.edu.cn",
    "mks.cumt.edu.cn",
    "sfs.cumt.edu.cn",
    "design.cumt.edu.cn",
    "rwxy.cumt.edu.cn",
    "sport.cumt.edu.cn",
    "syq.cumt.edu.cn",
    "energy.cumt.edu.cn",
    "jitri.cumt.edu.cn",
    "sac.cumt.edu.cn",
    "sce.cumt.edu.cn",
    "hr.cumt.edu.cn",
)
LOCAL_ADVISOR_PATH = BASE_DIR / "data" / "advisor_fallback.md"
TITLE_WORDS = ("教授", "副教授", "讲师", "研究员", "副研究员", "博导", "硕导")
NAME_STOP_WORDS = {
    "中国矿业",
    "矿业大学",
    "计算机科",
    "安全工程",
    "矿业工程",
    "师资队伍",
    "教师队伍",
    "研究方向",
    "个人主页",
    "教师主页",
    "学院简介",
    "发布时间",
    "推荐理由",
    "匹配方向",
    "导师推荐",
    "职称",
    "学院",
    "部门",
    "智能系统",
    "智能控制",
    "控制系统",
    "先进控制",
    "信息控制",
    "研究团队",
    "科研团队",
    "部门智能",
    "模式识别",
    "机械工程",
    "机械电气",
    "计算机科",
    "相关教师",
    "教师",
    "学院相关",
}
DOMAIN_DEPARTMENTS = {
    "cs.cumt.edu.cn": "计算机科学与技术学院/人工智能学院",
    "safe.cumt.edu.cn": "安全工程学院",
    "cese.cumt.edu.cn": "矿业工程学院",
    "cace.cumt.edu.cn": "力学与土木工程学院",
    "cmee.cumt.edu.cn": "机电工程学院",
    "siee.cumt.edu.cn": "信息与控制工程学院",
    "sres.cumt.edu.cn": "资源与地球科学学院",
    "scet.cumt.edu.cn": "化工学院",
    "cesi.cumt.edu.cn": "环境与测绘学院",
    "see.cumt.edu.cn": "电气工程学院",
    "slepe.cumt.edu.cn": "低碳能源与动力工程学院",
    "smsp.cumt.edu.cn": "材料与物理学院",
    "math.cumt.edu.cn": "数学学院",
    "sm.cumt.edu.cn": "经济管理学院",
    "cllp.cumt.edu.cn": "公共管理学院（应急管理学院）",
    "mks.cumt.edu.cn": "马克思主义学院",
    "sfs.cumt.edu.cn": "外国语言文化学院",
    "design.cumt.edu.cn": "建筑与设计学院",
    "rwxy.cumt.edu.cn": "人文与艺术学院",
    "sport.cumt.edu.cn": "体育学院",
    "syq.cumt.edu.cn": "孙越崎学院",
    "energy.cumt.edu.cn": "能源学院",
    "jitri.cumt.edu.cn": "国家卓越工程师学院",
    "sac.cumt.edu.cn": "国际学院",
    "sce.cumt.edu.cn": "继续教育学院",
}
TARGET_COLLEGES = (
    "矿业工程学院",
    "安全工程学院",
    "力学与土木工程学院",
    "机电工程学院",
    "信息与控制工程学院",
    "资源与地球科学学院",
    "化工学院",
    "环境与测绘学院",
    "电气工程学院",
    "低碳能源与动力工程学院",
    "材料与物理学院",
    "数学学院",
    "计算机科学与技术学院",
    "人工智能学院",
    "经济管理学院",
    "公共管理学院",
    "应急管理学院",
    "马克思主义学院",
    "外国语言文化学院",
    "建筑与设计学院",
    "人文与艺术学院",
    "体育学院",
    "孙越崎学院",
    "未来技术学院",
    "能源学院",
    "国家卓越工程师学院",
    "国际学院",
    "继续教育学院",
)
COLLEGE_DOMAINS = {
    "矿业工程学院": "cese.cumt.edu.cn",
    "安全工程学院": "safe.cumt.edu.cn",
    "力学与土木工程学院": "cace.cumt.edu.cn",
    "机电工程学院": "cmee.cumt.edu.cn",
    "信息与控制工程学院": "siee.cumt.edu.cn",
    "资源与地球科学学院": "sres.cumt.edu.cn",
    "化工学院": "scet.cumt.edu.cn",
    "环境与测绘学院": "cesi.cumt.edu.cn",
    "电气工程学院": "see.cumt.edu.cn",
    "低碳能源与动力工程学院": "slepe.cumt.edu.cn",
    "材料与物理学院": "smsp.cumt.edu.cn",
    "数学学院": "math.cumt.edu.cn",
    "计算机科学与技术学院": "cs.cumt.edu.cn",
    "人工智能学院": "cs.cumt.edu.cn",
    "经济管理学院": "sm.cumt.edu.cn",
    "公共管理学院": "cllp.cumt.edu.cn",
    "应急管理学院": "cllp.cumt.edu.cn",
    "马克思主义学院": "mks.cumt.edu.cn",
    "外国语言文化学院": "sfs.cumt.edu.cn",
    "建筑与设计学院": "design.cumt.edu.cn",
    "人文与艺术学院": "rwxy.cumt.edu.cn",
    "体育学院": "sport.cumt.edu.cn",
    "孙越崎学院": "syq.cumt.edu.cn",
    "未来技术学院": "syq.cumt.edu.cn",
    "能源学院": "energy.cumt.edu.cn",
    "国家卓越工程师学院": "jitri.cumt.edu.cn",
    "国际学院": "sac.cumt.edu.cn",
    "继续教育学院": "sce.cumt.edu.cn",
}
DEFAULT_FOCUSED_COLLEGES = (
    "矿业工程学院",
    "安全工程学院",
    "信息与控制工程学院",
    "机电工程学院",
    "计算机科学与技术学院",
    "人工智能学院",
    "电气工程学院",
    "资源与地球科学学院",
)
CS_FALLBACK_KEYWORDS = (
    "计算机",
    "软件",
    "人工智能",
    "AI",
    "机器学习",
    "深度学习",
    "计算机视觉",
    "图像",
    "算法",
    "大模型",
    "NLP",
    "自然语言",
    "知识图谱",
    "数据挖掘",
    "网络安全",
    "信息安全",
)
KEYWORD_COLLEGE_RULES = (
    (("矿院", "矿业", "采矿", "煤矿", "矿井", "智能采矿", "矿山"), ("矿业工程学院", "安全工程学院", "资源与地球科学学院")),
    (("安全", "瓦斯", "灾害", "风险", "预警", "应急"), ("安全工程学院", "公共管理学院", "应急管理学院")),
    (("机器人", "无人", "巡检", "机械", "装备"), ("机电工程学院", "信息与控制工程学院", "计算机科学与技术学院")),
    (("控制", "自动化", "传感", "物联网", "边缘", "通信", "信号"), ("信息与控制工程学院", "电气工程学院", "计算机科学与技术学院")),
    (("视觉", "图像", "深度学习", "人工智能", "算法", "软件", "数据", "知识图谱", "大模型"), ("计算机科学与技术学院", "人工智能学院", "数学学院")),
    (("地质", "资源", "测绘", "遥感", "环境"), ("资源与地球科学学院", "环境与测绘学院")),
    (("化工", "材料", "能源", "低碳", "动力"), ("化工学院", "材料与物理学院", "低碳能源与动力工程学院", "能源学院")),
    (("土木", "力学", "建筑", "结构"), ("力学与土木工程学院", "建筑与设计学院")),
    (("管理", "经济", "评价", "决策", "公共"), ("经济管理学院", "公共管理学院", "应急管理学院")),
    (("外语", "语言", "文化", "人文", "艺术", "体育", "马克思"), ("外国语言文化学院", "人文与艺术学院", "体育学院", "马克思主义学院")),
)
BAD_NAME_FRAGMENTS = (
    "学院",
    "大学",
    "方向",
    "主页",
    "队伍",
    "系统",
    "控制",
    "工程",
    "团队",
    "研究",
    "信息",
    "智能",
    "机械",
    "电气",
    "模式",
    "识别",
    "计算机",
    "相关",
    "教师",
)
ALLOWED_DEPARTMENT_KEYWORDS = (
    "计算机科学与技术学院",
    "人工智能学院",
    "安全工程学院",
    "矿业工程学院",
    "力学与土木工程学院",
    "机电工程学院",
    "信息与控制工程学院",
    "资源与地球科学学院",
    "化工学院",
    "环境与测绘学院",
    "电气工程学院",
    "低碳能源与动力工程学院",
    "材料与物理学院",
    "数学学院",
    "经济管理学院",
    "公共管理学院",
    "应急管理学院",
    "马克思主义学院",
    "外国语言文化学院",
    "建筑与设计学院",
    "人文与艺术学院",
    "体育学院",
    "孙越崎学院",
    "未来技术学院",
    "能源学院",
    "国家卓越工程师学院",
    "国际学院",
    "继续教育学院",
)
BLOCKED_DEPARTMENT_KEYWORDS = (
    "中国矿业大学北京",
    "北京",
    "机械与电气工程学院",
)


def select_target_colleges(topic: str, college: str, limit: int = 9) -> list[str]:
    text = f"{topic} {college}"
    picked: list[str] = []

    def add(name: str) -> None:
        if name and name not in picked:
            picked.append(name)

    if college:
        matched = False
        for item in TARGET_COLLEGES:
            if college in item or item in college:
                add(item)
                matched = True
        if not matched:
            add(college)

    for keywords, colleges in KEYWORD_COLLEGE_RULES:
        if any(keyword in text for keyword in keywords):
            for item in colleges:
                add(item)

    for item in DEFAULT_FOCUSED_COLLEGES:
        add(item)

    return picked[:limit]


def should_use_local_cs_fallback(topic: str, college: str) -> bool:
    text = f"{topic} {college}"
    return any(keyword in text for keyword in CS_FALLBACK_KEYWORDS)


def build_queries(topic: str, school: str, college: str, domains: list[str]) -> list[str]:
    topic = topic.strip()
    school = school.strip()
    college = college.strip()
    domain_query = " OR ".join(f"site:{domain}" for domain in domains)
    colleges = select_target_colleges(topic, college)
    queries: list[str] = []
    for item in colleges:
        domain = COLLEGE_DOMAINS.get(item, "")
        scope = f"site:{domain}" if domain else domain_query
        queries.extend(
            [
                f"{scope} {school} 徐州 {item} {topic} 教授 副教授 教师",
                f"{scope} {item} {topic} 教师简介 导师队伍",
            ]
        )
    queries.extend(
        [
            f"site:cs.cumt.edu.cn/szdw {topic} 学院教师",
            f"site:safe.cumt.edu.cn {topic} 安全工程学院 教授 副教授 教师",
            f"site:cese.cumt.edu.cn {topic} 矿业工程学院 教授 副教授 教师",
            f"{domain_query} {school} 徐州 {topic} 教授 副教授 教师 研究方向",
            f"site:faculty.cumt.edu.cn {school} {topic} 教师 研究方向",
        ]
    )
    return list(dict.fromkeys(queries))


def official_score(url: str, domains: list[str]) -> int:
    lowered = url.lower()
    for domain in domains:
        if domain.lower() in lowered:
            return 2
    return 0


def extract_name(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    patterns = [
        r"([\u4e00-\u9fff]{2,4})(?:教授|副教授|讲师|研究员|副研究员|老师|教师)",
        r"([\u4e00-\u9fff]{2,4})[-_｜|—]",
        r"^([\u4e00-\u9fff]{2,4})\s",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match and is_plausible_name(match.group(1)):
            return match.group(1)
    return ""


def is_plausible_name(name: str) -> bool:
    if not re.fullmatch(r"[\u4e00-\u9fff]{2,4}", name):
        return False
    return name not in NAME_STOP_WORDS and not any(word in name for word in BAD_NAME_FRAGMENTS)


def extract_title(text: str) -> str:
    found = [word for word in TITLE_WORDS if word in text]
    return "、".join(found[:2])


def department_from_url(url: str) -> str:
    lowered = url.lower()
    for domain, department in DOMAIN_DEPARTMENTS.items():
        if domain in lowered:
            return department
    return ""


def clean_department(value: str) -> str:
    value = re.sub(r"\s+", "", value or "")
    value = value.strip(" ：:，,。；;|｜-—–")
    for keyword in ALLOWED_DEPARTMENT_KEYWORDS:
        if keyword in value:
            return keyword
    if value in {"学院", "部门", "导师队伍", "师资队伍", "教师简介"}:
        return ""
    return value


def is_valid_department(value: str) -> bool:
    value = clean_department(value)
    if not value or any(token in value for token in BLOCKED_DEPARTMENT_KEYWORDS):
        return False
    return any(token in value for token in ALLOWED_DEPARTMENT_KEYWORDS)


def extract_department(text: str, college: str, url: str = "") -> str:
    if college and college in text:
        return college
    from_url = department_from_url(url)
    if from_url:
        return from_url
    match = re.search(r"([\u4e00-\u9fff]{2,18}(?:学院|系|中心|实验室))", text)
    value = match.group(1) if match else ""
    return clean_department(value)


def normalize_item(item: dict[str, Any], domains: list[str], school: str, college: str) -> dict[str, Any]:
    title = item.get("title", "") or ""
    url = item.get("url", "") or ""
    snippet = item.get("snippet", "") or ""
    text = f"{title} {snippet}"
    return {
        "name": extract_name(text),
        "title": extract_title(text),
        "department": extract_department(text, college, url),
        "direction": snippet[:180],
        "source_title": title,
        "url": url,
        "school": school,
        "official_score": official_score(url, domains),
        "verification": "official-domain" if official_score(url, domains) >= 1 else "needs-check",
    }


def useful_page_url(url: str) -> bool:
    lowered = url.lower()
    blocked = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".rar")
    return bool(url) and not any(lowered.endswith(ext) for ext in blocked)


def extract_names_from_line(line: str) -> list[str]:
    names: list[str] = []
    cleaned = re.sub(r"[（(]准聘[^）)]*[）)]", "", line)
    for name in re.findall(r"[\u4e00-\u9fff]{2,4}", cleaned):
        if is_plausible_name(name) and name not in names:
            names.append(name)
    return names


def extract_page_advisors(page: dict[str, Any], domains: list[str], school: str, college: str, topic: str) -> list[dict[str, Any]]:
    text = page.get("text", "") or ""
    title = page.get("title", "") or ""
    url = page.get("url", "") or ""
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    topic_tokens = [token for token in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_+-]{2,}", topic) if len(token) >= 2]
    current_title = ""
    department = extract_department(title, college, url)

    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line.strip())
        if not line or len(line) > 240:
            continue
        if any(token in line for token in ("教授", "副教授", "讲师", "研究员", "师资博士后")) and len(line) <= 24:
            current_title = line.strip(" ：:")
            continue
        if current_title and len(line) <= 80:
            for name in extract_names_from_line(line):
                if name in seen:
                    continue
                seen.add(name)
                candidates.append(
                    {
                        "name": name,
                        "title": current_title,
                        "department": department,
                        "direction": "",
                        "source_title": title or "官网师资页",
                        "url": url,
                        "school": school,
                        "official_score": official_score(url, domains) + 1,
                        "verification": "official-page-extracted",
                    }
                )
            continue
        if not any(word in line for word in TITLE_WORDS + ("导师", "教师", "研究方向", "个人简介", "主页")):
            continue
        name = extract_name(line)
        if not name or name in seen:
            continue
        seen.add(name)
        title_text = extract_title(line)
        direction = line
        if topic_tokens and not any(token in line for token in topic_tokens):
            direction = line
        candidates.append(
            {
                "name": name,
                "title": title_text,
                "department": extract_department(f"{title} {line}", college, url),
                "direction": direction[:180],
                "source_title": title or "官网师资页",
                "url": url,
                "school": school,
                "official_score": official_score(url, domains) + 1,
                "verification": "official-page-extracted",
            }
        )
    return candidates


def tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_+-]{2,}", text) if len(token) >= 2]


def advisor_search_url(name: str, school: str, college: str) -> str:
    search_college = college or "计算机科学与技术学院"
    query = quote_plus(f"site:cs.cumt.edu.cn {school} 徐州 {search_college} {name} 教师")
    return f"https://www.baidu.com/s?wd={query}"


def load_local_advisors(school: str, college: str) -> list[dict[str, Any]]:
    if not LOCAL_ADVISOR_PATH.exists():
        return []
    text = LOCAL_ADVISOR_PATH.read_text(encoding="utf-8")
    advisors: list[dict[str, Any]] = []
    current_title = ""
    current: dict[str, Any] | None = None

    def push() -> None:
        if current and current.get("name"):
            name = str(current["name"])
            if not current.get("department"):
                current["department"] = college or "计算机科学与技术学院"
            current.setdefault("url", advisor_search_url(name, school, college))
            current.setdefault("source_title", "校内导师候选库")
            current.setdefault("school", school)
            current.setdefault("official_score", 0)
            current.setdefault("verification", "advisor-candidate")
            advisors.append(dict(current))

    for raw in text.splitlines():
        line = raw.strip()
        section = re.match(r"^##\s+(.+)$", line)
        if section:
            current_title = section.group(1).strip()
            continue
        name_match = re.match(r"^###\s+([\u4e00-\u9fff]{2,4})", line)
        if name_match:
            push()
            name = name_match.group(1)
            current = {
                "name": name,
                "department": college or "计算机科学与技术学院",
                "title": current_title if current_title not in {"教授", "副教授", "讲师"} else current_title,
                "direction": "",
                "url": advisor_search_url(name, school, college),
                "source_title": "校内导师候选库",
                "school": school,
                "official_score": 0,
                "verification": "advisor-candidate",
            }
            continue
        if current is None:
            continue
        if line.startswith("- 职称："):
            current["title"] = line.split("：", 1)[1].strip()
        elif line.startswith("- 研究方向："):
            current["direction"] = line.split("：", 1)[1].strip()
    push()
    return advisors


def local_fallback_advisors(topic: str, school: str, college: str, limit: int) -> list[dict[str, Any]]:
    if not should_use_local_cs_fallback(topic, college):
        return []
    advisors = load_local_advisors(school, college)
    if not advisors:
        return []
    query_tokens = set(tokenize(topic))
    scored: list[tuple[int, dict[str, Any]]] = []
    for advisor in advisors:
        text = " ".join(str(advisor.get(key, "")) for key in ("name", "title", "direction", "department"))
        tokens = set(tokenize(text))
        score = len(query_tokens & tokens)
        for strong in ("计算机视觉", "深度学习", "机器人", "物联网", "边缘计算", "矿山", "矿井", "安全", "煤矿"):
            if strong in topic and strong in text:
                score += 3
        scored.append((score, advisor))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item for score, item in scored if score > 0][:limit] or [item for _, item in scored[: min(3, limit)]]


def diversify_advisors(items: list[dict[str, Any]], limit: int, max_per_department: int = 2) -> list[dict[str, Any]]:
    picked: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    overflow: list[dict[str, Any]] = []
    for item in items:
        department = str(item.get("department", "")).strip()
        if counts.get(department, 0) < max_per_department:
            picked.append(item)
            counts[department] = counts.get(department, 0) + 1
        else:
            overflow.append(item)
        if len(picked) >= limit:
            return picked
    for item in overflow:
        if len(picked) >= limit:
            break
        picked.append(item)
    return picked[:limit]


def search_advisors(
    topic: str,
    school: str,
    college: str,
    domains: list[str],
    max_results: int,
    timeout: int,
    open_pages: int,
    local_fallback: bool,
) -> dict[str, Any]:
    queries = build_queries(topic, school, college, domains)
    local_pool = local_fallback_advisors(topic, school, college, max_results) if local_fallback else []
    candidates: list[dict[str, Any]] = []
    pages_to_open: list[dict[str, Any]] = []
    seen: set[str] = set()
    errors: list[dict[str, str]] = []
    opened_pages: list[dict[str, str]] = []

    for query in queries:
        try:
            result = web_search.web_search(query, max_results=max_results, timeout=timeout)
        except Exception as exc:
            errors.append({"query": query, "error": str(exc)})
            continue
        for item in result.get("results", []):
            normalized = normalize_item(item, domains, school, college)
            if normalized.get("official_score", 0) < 1 or not useful_page_url(str(normalized.get("url", ""))):
                continue
            pages_to_open.append(normalized)
            if not normalized.get("name"):
                continue
            key = normalized["url"] or normalized["source_title"]
            if not key or key in seen:
                continue
            seen.add(key)
            candidates.append(normalized)

    if open_link is not None and open_pages > 0:
        page_seen: set[str] = set()
        official_pages: list[dict[str, Any]] = []
        for item in pages_to_open:
            url = str(item.get("url", ""))
            if url and url not in page_seen:
                page_seen.add(url)
                official_pages.append(item)
        for item in official_pages[:open_pages]:
            url = str(item.get("url", ""))
            try:
                page = open_link.open_link(url, timeout=timeout)
            except Exception as exc:
                opened_pages.append({"url": url, "status": "error", "error": str(exc)})
                continue
            opened_pages.append({"url": url, "status": str(page.get("status", "unknown"))})
            if page.get("status") != "success":
                continue
            for extracted in extract_page_advisors(page, domains, school, college, topic):
                key = f"{extracted.get('name')}|{extracted.get('url')}"
                if not extracted.get("name") or key in seen:
                    continue
                seen.add(key)
                candidates.append(extracted)

    online_candidates = [
        item
        for item in candidates
        if (
            item.get("name")
            and is_plausible_name(str(item.get("name", "")))
            and is_valid_department(str(item.get("department", "")))
            and str(item.get("url", "")).startswith(("http://", "https://"))
            and item.get("official_score", 0) >= 1
        )
    ]
    online_candidates.sort(key=lambda item: (item.get("official_score", 0), bool(item.get("title"))), reverse=True)
    local_candidates: list[dict[str, Any]] = []
    if local_fallback and len(online_candidates) < min(3, max_results):
        existing_names = {str(item.get("name", "")) for item in online_candidates}
        need = min(2, max_results - len(online_candidates))
        local_candidates = [item for item in local_pool if item.get("name") not in existing_names][:need]

    final_candidates = diversify_advisors(online_candidates + local_candidates, max_results)
    status = "success" if online_candidates else "local_fallback"
    if online_candidates and local_candidates:
        status = "partial_local_fallback"
    return {
        "status": status,
        "source": "official-advisor-search",
        "topic": topic,
        "school": school,
        "college": college,
        "domains": domains,
        "queries": queries,
        "opened_pages": opened_pages,
        "errors": errors,
        "count": len(final_candidates),
        "results": final_candidates,
        "online_count": len(online_candidates),
        "local_count": len(local_candidates),
        "note": "优先使用矿大徐州官网；官网结果不足时补充校内导师候选，并提供官网限定搜索链接。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search official university pages for advisor candidates.")
    parser.add_argument("topic", help="Research topic or direction")
    parser.add_argument("--school", default="中国矿业大学")
    parser.add_argument("--college", default="")
    parser.add_argument("--domains", default=",".join(DEFAULT_DOMAINS), help="Comma-separated official domains")
    parser.add_argument("--max-results", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--open-pages", type=int, default=3, help="Open top official pages to extract more advisor names")
    parser.add_argument("--no-open-pages", action="store_true", help="Only use search result snippets")
    parser.add_argument("--no-local-fallback", action="store_true", help="Disable local advisor reference fallback")
    args = parser.parse_args()

    domains = [item.strip() for item in args.domains.split(",") if item.strip()]
    open_pages = 0 if args.no_open_pages else max(args.open_pages, 0)
    result = search_advisors(
        args.topic,
        args.school,
        args.college,
        domains,
        args.max_results,
        args.timeout,
        open_pages,
        not args.no_local_fallback,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
