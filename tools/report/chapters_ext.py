"""Các mục bổ sung của báo cáo (đợt 2): lưu trữ, giao diện, ShopLab, RQ1 chất lượng test, RQ2 bản 2, RQ3, RQ4.

Mọi số liệu đọc từ file kết quả JSON; phần nhận xét viết tay nằm trong notes_ext.py.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
IMG = ROOT / "docs/bao-cao-chuyen-de/img"
sys.path.insert(0, str(ROOT))

from apps.shoplab.suite import SUITE  # noqa: E402
from apps.shoplab.variants import VARIANTS  # noqa: E402


def pct(a, b):
    return f"{a / b * 100:.0f}%" if b else "—"


def mcnemar(b: int, c: int) -> float:
    n, k = b + c, min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


def load(name: str):
    p = ROOT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# ======================= Chương 3 =======================
def storage_section(r):
    r.h2("3.9 Lưu trữ và repository")
    r.p("Lớp lưu trữ dùng SQLAlchemy 2, chạy trên SQLite khi phát triển và kiểm thử, và trên SQL Server Express khi demo; "
        "đổi giữa hai DB chỉ cần biến môi trường DATABASE_URL. Schema bám các entity trong kiến trúc (Bảng 3.7) theo ba "
        "nguyên tắc. Một là artifact có thể sửa sau review (yêu cầu, test case, script) có cột version: lưu lại cùng nội "
        "dung thì giữ version cũ, nội dung đổi thì thêm một dòng version + 1, không ghi đè. Hai là quyết định duyệt, lần "
        "chạy, đề xuất sửa và sự kiện giao diện chỉ được thêm, không có API sửa hay xoá. Ba là nội dung có cấu trúc lưu "
        "dạng JSON để dùng lại đúng model Pydantic của agent, không phải ánh xạ từng trường sang cột. Mọi cột chuỗi dùng kiểu Unicode (NVARCHAR trên SQL Server). Khi chạy bộ "
        "test repository trên SQL Server, bản đầu dùng VARCHAR làm mất dấu tiếng Việt (\"Đăng nhập\" thành \"?ang nh?p\"), so "
        "sánh nội dung sai nên version tăng oan; lỗi này không lộ ra trên SQLite.")
    r.table("Các bảng trong cơ sở dữ liệu", ["Bảng", "Nội dung", "Kiểu ghi"], [
        ["project", "Dự án và URL ứng dụng đích", "tạo một lần"],
        ["requirement_version", "Yêu cầu đã chuẩn hoá (JSON StructuredRequirement)", "có version"],
        ["test_case_version", "Test case (JSON TestCase), gắn requirement_id", "có version"],
        ["approval_decision", "Cổng, artifact, version, quyết định, người duyệt, lý do", "append-only"],
        ["generated_script", "Plan (JSON), mã Python, kết quả grounding", "có version"],
        ["execution_run", "Trạng thái, mã thoát, stderr, đường dẫn ảnh chụp", "append-only"],
        ["repair_proposal", "Đề xuất sửa (rủi ro, diff, loại thay đổi, plan mới)", "append-only"],
        ["trace_link", "Liên kết nguồn → đích và loại quan hệ", "thêm khi lưu artifact"],
        ["ui_event", "Thao tác trên giao diện theo phiên và người dùng (dữ liệu RQ4)", "append-only"],
    ], [4, 8.5, 3.5])
    r.p("Repository (src/repositories/store.py) là đường truy cập dữ liệu duy nhất của giao diện: nhận và trả model "
        "Pydantic, giấu bảng SQLAlchemy phía sau. Trace link được tạo tự động khi lưu artifact: requirement verified_by "
        "test_case, test_case implemented_by script@vN, test_case executed_as execution, execution repaired_by repair. Một "
        "vòng sửa lỗi vì vậy để lại đủ chuỗi để truy ngược từ đề xuất sửa về yêu cầu gốc.")


def ui_section(r):
    r.h2("3.10 Giao diện người dùng")
    r.p("Giao diện Streamlit (src/ui/app.py) đi theo đúng luồng của Hình 3.2 và ghi mọi quyết định vào DB. Thanh bên chọn "
        "người dùng, dự án, URL ứng dụng đích, backend LLM và nguồn tài liệu. Tab Quy trình có bốn bước: ① yêu cầu và "
        "cổng AG-01 (Hình 3.3); ② test case, sửa được thành version mới, và cổng AG-02; ③ sinh script và chạy; ④ sửa "
        "lỗi có ràng buộc. Tab Lịch sử hiển thị số liệu, chuỗi truy vết, các quyết định và thao tác của phiên (Hình 3.5).")
    r.figure(str(IMG / "1_requirements.png"), "Bước ①: yêu cầu trích xuất, cờ mơ hồ và nút duyệt AG-01", width_cm=15)
    r.p("Ở bước ③, nút Sinh script chạy đúng quy trình DOM-aware có vòng lặp grounding của mục 3.5.4: chụp aria snapshot "
        "trang đích, gọi LLM, đếm phần tử khớp trên trang thật, sinh lại một lần nếu có locator khớp khác 1. Người dùng "
        "xem bảng grounding, mã sinh ra và ảnh chụp sau khi chạy, và có thể sửa plan JSON trực tiếp (mỗi lần lưu là một "
        "version script mới). Ở bước ④, mỗi test lỗi có nút Đề xuất sửa. Đề xuất hiển thị mức rủi ro, cổng duyệt tương "
        "ứng, loại thay đổi, lý do và diff (Hình 3.4). Đề xuất làm đổi ý nghĩa test có cảnh báo đỏ. Chỉ khi người dùng "
        "bấm Duyệt và chạy lại, plan mới mới được lưu thành version script mới và chạy lại.")
    r.figure(str(IMG / "3_repair.png"), "Bước ④: đề xuất sửa từ self-healing, rủi ro Low, chờ người duyệt", width_cm=15)
    r.table("Ánh xạ đề xuất sửa sang cổng duyệt", ["Loại thay đổi trong đề xuất", "Cổng", "Ý nghĩa"], [
        ["Bỏ, thêm, đổi loại bước; đổi dữ liệu nhập hoặc URL điều hướng", "AG-05", "Đổi bước kiểm thử"],
        ["Assertion đổi giá trị kỳ vọng", "AG-04", "Đổi oracle / expected result"],
        ["Assertion giữ giá trị nhưng đổi phần tử được kiểm", "AG-03", "Đổi assertion"],
        ["Chỉ đổi locator của thao tác", "REPAIR-LOW", "Duyệt đơn giản"],
    ], [7.5, 2.5, 6])
    r.figure(str(IMG / "4_history.png"), "Tab Lịch sử: chuỗi truy vết tới script v3 và đề xuất sửa, quyết định append-only",
             width_cm=15)
    r.p("Playwright sync API chạy trong tiến trình Streamlit trên Windows dễ xung đột event loop. Các tác vụ trình duyệt "
        "(chụp snapshot, grounding, dò bước hỏng và tự chữa) vì vậy chạy ở tiến trình con qua src/services/browser_tasks.py; "
        "harness RQ3 gọi cùng các hàm này trực tiếp trong tiến trình của nó. Luồng giao diện được kiểm bằng một kịch bản "
        "Playwright đi hết các bước: chạy đạt, cố ý làm hỏng plan, chạy trượt, nhận đề xuất sửa, duyệt và chạy lại đạt.")


# ======================= Chương 4 =======================
def shoplab_section(r):
    r.h2("4.2 ShopLab: ứng dụng đích có mutation kiểm soát được")
    r.p("Các site demo công khai không cho phép thay đổi giao diện hay nghiệp vụ theo ý muốn, nên không dùng được để đo "
        "khả năng sửa lỗi. Nhóm xây ShopLab (apps/shoplab, Flask, khoảng 200 dòng) gồm đăng nhập, danh sách sản phẩm, "
        "giỏ hàng, checkout và hồ sơ. Mọi id, nhãn, placeholder, chữ trên nút, thông báo và cờ hành vi đọc từ cấu hình "
        "của biến thể. Mỗi biến thể là phiên bản gốc v0 cộng một nhóm thay đổi, có nhãn ground truth (Bảng 4.1).")
    rows = [[name, v["kind"], v["desc"]] for name, v in VARIANTS.items() if name != "v0"]
    r.table(f"{len(rows)} biến thể (mutation) của ShopLab; T9–T12 và S7–S10 là tập độc lập", ["Biến thể", "Lớp", "Thay đổi"],
            rows, [3.6, 2.4, 10], center_cols=(1,))
    r.p("Lớp technical là refactor giao diện, nghiệp vụ giữ nguyên: hành vi đúng của cơ chế sửa là tìm lại phần tử, test "
        "pass, assertion giữ nguyên. Lớp semantic là thay đổi hành vi nghiệp vụ, tương đương một bug thật: test fail là "
        "đúng, và hành vi đúng của cơ chế sửa là không được làm test pass. Bộ test gồm 20 test viết cho v0, cố ý dùng trộn "
        "các chiến lược locator (css id, placeholder, label, role, test id, class) như một bộ test thực tế, để mỗi mutation "
        "làm gãy một tập test khác nhau. Lệnh run_rq3.py --check kiểm rằng 20/20 test pass trên v0 và mỗi mutation làm "
        "gãy ít nhất một test.")
    r.p("Trong lần kiểm đầu, mutation đổi placeholder \"Username\" thành \"Enter your username\" không làm gãy test nào: "
        "get_by_placeholder khớp theo chuỗi con, không phân biệt hoa thường. Đây là một tính năng chịu lỗi có thật của "
        "Playwright. Biến thể được đổi sang placeholder không chứa từ cũ (\"Your login\").")


def rq3_method(r, broken_counts: dict | None):
    r.h2("4.5 Đánh giá RQ3: sửa lỗi có ràng buộc")
    r.p("Mỗi cặp (test, mutation) mà test gãy là một ca sửa lỗi. Để mutation làm gãy nhiều test (T4 làm gãy 17, S4 làm gãy "
        "12) không lấn át số liệu, mỗi mutation lấy tối đa 6 test gãy đầu tiên theo thứ tự cố định. Mỗi ca được chạy qua "
        "ba nhánh (Bảng 4.3), cùng ngân sách 2 lần sửa và cùng bằng chứng: stderr và aria snapshot của trang tại bước hỏng.")
    r.table("Ba nhánh sửa lỗi của RQ3", ["Nhánh", "Cách sửa", "Áp dụng đề xuất"], [
        ["unconstrained", "LLM với prompt \"làm test PASS, được đổi mọi action kể cả assertion\" (mô phỏng autonomous repair [8])",
         "Tự áp dụng mọi đề xuất"],
        ["heal", "Chỉ self-healing tất định từ DOM sống, không LLM", "Áp dụng (luôn là rủi ro Low)"],
        ["constrained", "Hệ thống: self-healing trước, LLM có ràng buộc sau; repair_policy phân mức",
         "Người duyệt mô phỏng duyệt Low; Medium, High và blocked chuyển lên người"],
    ], [2.8, 8.2, 5])
    if broken_counts:
        r.p("Số ca theo mutation: " + "; ".join(f"{v} {n}" for v, n in broken_counts.items()) + ".")
    r.p("Số đo: số mutation technical sửa được mà không làm yếu assertion; số mutation semantic bị che (sau sửa test "
        "pass dù app đang lỗi); số lần làm yếu assertion (đề xuất được áp dụng có đổi assertion, đổi loại action hoặc bỏ "
        "bước); số ca escalate lên người. Người duyệt mô phỏng là một giả định: trong thực tế người duyệt có thể duyệt cả "
        "đề xuất High (nếu yêu cầu thật sự đổi) hoặc từ chối cả đề xuất Low.")


def rq4_method(r):
    r.h2("4.6 Đánh giá RQ4: thí nghiệm có người tham gia")
    r.p("RQ4 cần đo công sức của người dùng, nên không mô phỏng được. Giao thức đầy đủ ở docs/development/rq4-protocol.md. "
        "Thiết kế trong-đối-tượng: mỗi người tham gia làm hai phiên 30 phút, một phiên tự viết test Playwright (được dùng "
        "codegen, không dùng trợ lý AI), một phiên dùng giao diện của hệ thống, trên hai bộ nhiệm vụ tương đương A và B "
        "(mỗi bộ 3 yêu cầu trên ShopLab). Thứ tự điều kiện và bộ nhiệm vụ được đảo cân bằng giữa người tham gia.")
    r.table("Số đo RQ4", ["Số đo", "Cách lấy"], [
        ["Thời gian hoàn thành", "Bấm giờ bằng tools/rq4/rq4.py timer"],
        ["Số yêu cầu có test hợp lệ (0–3)",
         "Tự chấm: test phải pass trên ShopLab v0 và fail trên mutation semantic phá đúng hành vi của yêu cầu đó"],
        ["Số lần sửa tay (điều kiện hệ thống)", "Sự kiện edit_test_case, edit_plan trong bảng ui_event"],
        ["Mức dễ dùng", "Phiếu SUS 10 câu (0–100)"],
    ], [5, 11])
    r.p("Tiêu chí test hợp lệ bắt được test chạy được nhưng không kiểm gì. Khi chạy thử bộ chấm, một test thêm sản phẩm "
        "vào giỏ mà không kiểm số trên giỏ được chấm không hợp lệ, vì nó vẫn pass trên mutation làm nút Add to cart vô "
        "hiệu. Hai điều kiện được chấm bằng cùng một bộ chấm.")
