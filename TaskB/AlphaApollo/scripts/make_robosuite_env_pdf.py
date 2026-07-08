#!/usr/bin/env python3
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.platypus import (
    Flowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "output" / "pdf"
OUT_PATH = OUT_DIR / "robosuite_env_classes_explained.pdf"


class ChainBox(Flowable):
    def __init__(self, items, width=16.2 * cm, row_h=0.82 * cm):
        super().__init__()
        self.items = items
        self.w = width
        self.row_h = row_h
        self.h = len(items) * row_h + (len(items) - 1) * 0.16 * cm

    def wrap(self, avail_width, avail_height):
        return min(self.w, avail_width), self.h

    def draw(self):
        c = self.canv
        box_w = self.w
        y = self.h - self.row_h
        for idx, (title, detail) in enumerate(self.items):
            c.setFillColor(colors.HexColor("#F4F7FA"))
            c.setStrokeColor(colors.HexColor("#9AAFC4"))
            c.roundRect(0, y, box_w, self.row_h, 4, fill=1, stroke=1)
            c.setFillColor(colors.HexColor("#1F2A37"))
            c.setFont("STSong-Light", 9.8)
            c.drawString(0.28 * cm, y + 0.47 * cm, title)
            c.setFillColor(colors.HexColor("#4B5563"))
            c.setFont("STSong-Light", 8.5)
            c.drawString(6.45 * cm, y + 0.47 * cm, detail)
            if idx < len(self.items) - 1:
                c.setStrokeColor(colors.HexColor("#6B7280"))
                x = box_w / 2
                c.line(x, y - 0.02 * cm, x, y - 0.14 * cm)
                c.line(x - 0.08 * cm, y - 0.08 * cm, x, y - 0.16 * cm)
                c.line(x + 0.08 * cm, y - 0.08 * cm, x, y - 0.16 * cm)
            y -= self.row_h + 0.16 * cm


def p(text, style):
    return Paragraph(text, style)


def bullets(items, style):
    return ListFlowable(
        [ListItem(Paragraph(item, style), leftIndent=8) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=14,
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    registerFont(UnicodeCIDFont("STSong-Light"))

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "CnTitle",
        parent=styles["Title"],
        fontName="STSong-Light",
        fontSize=22,
        leading=28,
        textColor=colors.HexColor("#111827"),
        spaceAfter=12,
    )
    h1 = ParagraphStyle(
        "CnH1",
        parent=styles["Heading1"],
        fontName="STSong-Light",
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#0F3D5E"),
        spaceBefore=10,
        spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "CnH2",
        parent=styles["Heading2"],
        fontName="STSong-Light",
        fontSize=12.5,
        leading=17,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=8,
        spaceAfter=5,
    )
    body = ParagraphStyle(
        "CnBody",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=10.2,
        leading=15.2,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=6,
    )
    small = ParagraphStyle(
        "CnSmall",
        parent=body,
        fontSize=8.6,
        leading=12.2,
        textColor=colors.HexColor("#4B5563"),
    )
    code = ParagraphStyle(
        "Code",
        parent=body,
        fontName="Courier",
        fontSize=8.1,
        leading=10.6,
        backColor=colors.HexColor("#F3F4F6"),
        borderColor=colors.HexColor("#D1D5DB"),
        borderWidth=0.4,
        borderPadding=5,
        textColor=colors.HexColor("#111827"),
        spaceBefore=4,
        spaceAfter=8,
    )

    doc = SimpleDocTemplate(
        str(OUT_PATH),
        pagesize=A4,
        rightMargin=1.55 * cm,
        leftMargin=1.55 * cm,
        topMargin=1.35 * cm,
        bottomMargin=1.35 * cm,
        title="TaskB Robosuite Env Classes Explained",
    )

    story = []
    story.append(p("TaskB Robosuite 环境里的类都是从哪里来的", title))
    story.append(
        p(
            "这份文档解释 run_taskB_robosuite_eval.py 里出现的 EmbodiedRobosuiteEnv、"
            "CodeExecEnvConfig、EmbodiedRobosuiteToolGroup 等对象分别是什么、定义在哪里、"
            "以及 env = EmbodiedRobosuiteEnv(cfg) 创建环境时它们如何连在一起。",
            body,
        )
    )

    story.append(p("1. 总体结构", h1))
    story.append(
        ChainBox(
            [
                (
                    "run_taskB_robosuite_eval.py",
                    "评测脚本: 创建 cfg, 创建 env, 循环调用模型和 env.step",
                ),
                (
                    "EmbodiedRobosuiteEnv",
                    "AlphaApollo 文本环境包装层: 解析 <python_code> 并组织多轮交互",
                ),
                (
                    "EmbodiedRobosuiteToolGroup",
                    "工具适配层: 把 python_code 工具映射到 capx_env.step(code)",
                ),
                (
                    "FrankaLiftCodeEnv 等 CaP-X Env",
                    "CaP-X 高层代码执行环境: 暴露 prompt, API, step(code)",
                ),
                (
                    "Robosuite low_level_env",
                    "底层仿真: 真实维护机器人、物体、奖励和终止状态",
                ),
            ]
        )
    )

    story.append(p("2. 关键对象速查表", h1))
    raw_data = [
        ["名字", "它是什么", "来源文件"],
        [
            "EmbodiedRobosuiteEnv",
            "AlphaApollo 的文本环境类。外层 env 就是它的实例。",
            "TaskB/AlphaApollo/.../embodied_robosuite/env.py",
        ],
        [
            "CodeExecEnvConfig",
            "CaP-X 的配置 dataclass。装 low_level 环境、API 列表、prompt 等。",
            "TaskA/cap-x/capx/envs/tasks/base.py",
        ],
        [
            "EmbodiedRobosuiteToolGroup",
            "AlphaApollo 工具组。提供 python_code 工具，用来执行模型代码。",
            "TaskB/AlphaApollo/.../core/tools/embodied_robosuite.py",
        ],
        [
            "ToolGroup / @tool",
            "AlphaApollo 的工具注册机制。@tool 标记的方法会被注册成可调用工具。",
            "TaskB/AlphaApollo/.../core/tools/core.py",
        ],
        [
            "FrankaLiftCodeEnv",
            "CaP-X 的 cube_lift 高层环境类，继承 CodeExecutionEnvBase。",
            "TaskA/cap-x/capx/envs/tasks/franka/franka_lift.py",
        ],
        [
            "FrankaPickPlaceCodeEnv",
            "CaP-X 的 cube_stack 高层环境类，继承 CodeExecutionEnvBase。",
            "TaskA/cap-x/capx/envs/tasks/franka/franka_pick_place.py",
        ],
        [
            "FrankaNutAssemblyCodeEnv",
            "CaP-X 的 peg_insertion 高层环境类，继承 CodeExecutionEnvBase。",
            "TaskA/cap-x/capx/envs/tasks/franka/franka_nut_assembly.py",
        ],
        [
            "CodeExecutionEnvBase",
            "CaP-X 高层代码执行基类。负责生成完整 prompt、绑定 API、执行代码。",
            "TaskA/cap-x/capx/envs/tasks/base.py",
        ],
    ]
    cell_style = ParagraphStyle(
        "Cell",
        parent=small,
        fontSize=7.6,
        leading=10.2,
        wordWrap="CJK",
    )
    head_style = ParagraphStyle(
        "HeadCell",
        parent=cell_style,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0F2F44"),
    )
    data = []
    for r, row in enumerate(raw_data):
        style = head_style if r == 0 else cell_style
        data.append([Paragraph(str(cell), style) for cell in row])
    table = Table(data, colWidths=[3.0 * cm, 6.3 * cm, 6.85 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCEAF5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F2F44")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#C9D2DC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)

    story.append(PageBreak())
    story.append(p("3. env = EmbodiedRobosuiteEnv(cfg) 发生了什么", h1))
    story.append(p("评测脚本中这一行会触发一串初始化。", body))
    story.append(p("env = EmbodiedRobosuiteEnv(cfg)", code))
    story.append(
        bullets(
            [
                "进入 EmbodiedRobosuiteEnv.__init__(env_config)。cfg 里有 task_name、max_steps、record_video、log_requests。",
                "调用 BaseTextEnv.__init__，初始化 turns、tool_groups、tool_to_toolgroup 等 AlphaApollo 文本环境字段。",
                "读取 task_name，决定要构建 cube_lift、cube_stack 还是 peg_insertion。",
                "调用 self._build_capx_env()，创建真正的 CaP-X high-level env 和 Robosuite low-level env。",
                "创建 EmbodiedRobosuiteToolGroup(self.capx_env)，把 CaP-X 环境包装成 AlphaApollo 工具。",
                "调用 self.init_tool_groups([self.tool_group])，把工具注册到外层环境里。",
                "最后 self.reset({})，让底层仿真环境进入初始状态并准备 task_prompt。",
            ],
            body,
        )
    )

    story.append(p("4. _build_capx_env 里面的对象来源", h1))
    story.append(
        p(
            "EmbodiedRobosuiteEnv 不是硬编码某一个任务类，而是通过 TASK_SPECS 根据 task_name 动态选择类。",
            body,
        )
    )
    story.append(
        p(
            '例如 cube_lift 使用 env_cls = "capx.envs.tasks.franka.franka_lift.FrankaLiftCodeEnv"，'
            'low_level_cls = "capx.envs.simulators.robosuite_cube_lift.FrankaRobosuiteCubeLiftLowLevel"，'
            'api = "FrankaControlPrivilegedApi"。',
            body,
        )
    )
    story.append(
        p(
            "动态导入由 _load_symbol 完成: 它把字符串路径切成模块名和类名，然后 import 模块，再 getattr 取出真正的类。",
            body,
        )
    )
    story.append(
        p(
            "low_level = low_level_cls(...) 先创建底层仿真。然后 CodeExecEnvConfig(...) 把 low_level 和 API 名字打包。"
            "最后 env_cls(cfg) 创建 CaP-X 高层环境。由于 FrankaLiftCodeEnv 等类没有自己的 __init__，"
            "所以会进入父类 CodeExecutionEnvBase.__init__(cfg)。",
            body,
        )
    )

    story.append(p("5. CodeExecEnvConfig 和 CodeExecutionEnvBase 的作用", h1))
    story.append(p("CodeExecEnvConfig 是一包配置，不负责执行。它主要包含:", h2))
    story.append(
        bullets(
            [
                "low_level: 已经构建好的 Robosuite 底层环境。",
                "apis: 要暴露给模型代码的 API 名字，比如 FrankaControlPrivilegedApi。",
                "prompt / oracle_code: 可选的任务说明和专家代码。",
                "privileged / enable_render: 影响 API 权限和渲染。",
            ],
            body,
        )
    )
    story.append(p("CodeExecutionEnvBase.__init__ 会把这些配置真正变成可运行环境:", h2))
    story.append(
        bullets(
            [
                "保存 cfg，并建立 self.low_level_env。",
                "根据 cfg.apis 创建 API 对象，并绑定到底层环境。",
                "生成完整 prompt: 任务说明 + API 文档。",
                "初始化执行上下文 self._exec_globals，把 env、APIS、get_object_pose、goto_pose 等放进去。",
                "提供 reset 和 step。step(code) 会 exec 模型生成的 Python 代码，然后计算 reward、terminated、truncated。",
            ],
            body,
        )
    )

    story.append(p("6. EmbodiedRobosuiteToolGroup 怎么把代码执行起来", h1))
    story.append(
        p(
            "EmbodiedRobosuiteToolGroup 是一个适配器。它本身不懂机器人控制细节，只保存 self.capx_env，"
            "并提供一个被 @tool 标记的方法 python_code(code)。",
            body,
        )
    )
    story.append(
        p(
            "当外层 env.step 解析出 <python_code> 里的代码后，会调用 AlphaApollo 的 _execute_tool。"
            "这个方法找到名为 EmbodiedRobosuiteToolGroup 的工具组，再调用其中的 python_code 工具。",
            body,
        )
    )
    story.append(
        p(
            "python_code 工具内部做的关键事情就是: self.capx_env.step(code)。"
            "CaP-X 执行代码后返回 obs、reward、terminated、truncated、info，工具组再把它们整理成 JSON 字符串。",
            body,
        )
    )

    story.append(p("7. 一轮 step 的完整数据流", h1))
    story.append(
        ChainBox(
            [
                ("模型返回", "<python_code> ... </python_code>"),
                ("ensure_python_code", "如果没有标签就补上标签"),
                ("EmbodiedRobosuiteEnv.step", "记录历史, 提取 python_code 里的代码"),
                ("_execute_tool", "按工具组名和工具名分发调用"),
                ("ToolGroup.python_code", "调用 capx_env.step(code)"),
                ("CodeExecutionEnvBase.step", "exec 代码, 控制 low_level_env, 计算 reward"),
                ("返回 step_out", "observation, reward, done, metadata"),
            ],
            row_h=0.74 * cm,
        )
    )

    story.append(p("8. 最短总结", h1))
    story.append(
        bullets(
            [
                "env 变量是 EmbodiedRobosuiteEnv 实例，是 AlphaApollo 外层文本环境。",
                "self.capx_env 是 CaP-X 高层代码执行环境，例如 FrankaLiftCodeEnv。",
                "self.capx_env.low_level_env 是真正的 Robosuite 仿真环境。",
                "EmbodiedRobosuiteToolGroup 是连接 AlphaApollo 工具调用和 CaP-X step(code) 的适配器。",
                "CodeExecEnvConfig 是传给 CaP-X 高层环境的配置包。",
                "CodeExecutionEnvBase 是真正准备 prompt、API、执行上下文并执行模型 Python 代码的基类。",
            ],
            body,
        )
    )

    story.append(Spacer(1, 0.2 * cm))
    story.append(
        p(
            "备注: 你的工作区里有多个 cap-x 副本。本文按当前讨论中定位到的 TaskA/cap-x 路径说明。"
            "如果运行时 PYTHONPATH 指向 cap-x(A) 或 test2/TaskA/cap-x，同名文件中的类结构基本对应，但实际源码位置会随导入路径变化。",
            small,
        )
    )

    def add_page_number(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("STSong-Light", 8)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawRightString(A4[0] - 1.55 * cm, 0.72 * cm, f"第 {doc_obj.page} 页")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(OUT_PATH)


if __name__ == "__main__":
    main()
