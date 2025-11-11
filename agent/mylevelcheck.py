import math
import logging
import json
import re  # 导入正则表达式模块
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context

# 为模块设置日志记录器
logger = logging.getLogger(__name__)

@AgentServer.custom_recognition("mylevelcheck")
class MyLevelCheck(CustomRecognition):
    """
    自定义识别模块: 在指定区域(ROI)内查找等级低于目标值的对象。

    通过解析 `custom_recognition_param` 字符串获取参数，
    以兼容当前版本的 MAA Agent 框架。
    """

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        
        # --- 步骤 1: 解析从 JSON 传入的参数字符串 ---
        param_str = argv.custom_recognition_param
        logger.debug(f"接收到原始参数字符串: '{param_str}'")

        try:
            params = json.loads(param_str) if param_str else {}
            # 增加健壮性检查：确保解析结果是一个字典
            if not isinstance(params, dict):
                params = {}
            target_level = params.get('target_level')
        except json.JSONDecodeError:
            logger.error(f"参数字符串 '{param_str}' 不是有效的 JSON 格式。")
            return CustomRecognition.AnalyzeResult(box=None, detail="Invalid params JSON")
        except Exception as e:
            logger.error(f"解析参数时发生未知错误: {e}")
            return CustomRecognition.AnalyzeResult(box=None, detail=f"Param parse error: {e}")

        if not isinstance(target_level, int):
            logger.error(f"参数 'target_level' 未提供或类型不正确 (需要整数)。")
            return CustomRecognition.AnalyzeResult(box=None, detail="target_level not found or not an integer")

        # --- 步骤 2: 验证并使用 ROI ---
        roi = argv.roi
        # roi 是一个 Rect 对象, 没有 len()。我们直接检查它是否存在。
        if not roi:
            logger.error(f"任务节点提供的 'roi' 参数无效: {roi}")
            return CustomRecognition.AnalyzeResult(box=None, detail="Invalid ROI")

        # 将 Rect 对象转换为 [x, y, w, h] 列表以用于日志和覆盖
        roi_list = [roi.x, roi.y, roi.w, roi.h]
        logger.info(f"开始等级检查: 目标等级 < {target_level}，扫描区域: {roi_list}")

        # --- 步骤 3: 在指定区域 (ROI) 内执行 OCR ---
        try:
            ocr_results = context.run_recognition(
                "OCR",  # 确保 pipeline 中有名为 "OCR" 的任务
                argv.image,
                pipeline_override={"OCR": {"roi": roi_list}}
            )
        except Exception as e:
            logger.error(f"调用 OCR 识别时发生异常: {e}")
            return CustomRecognition.AnalyzeResult(box=None, detail=f"OCR execution error: {e}")

        if not ocr_results or not ocr_results.filterd_results: 
            logger.warning(f"在区域 {roi_list} 内没有识别到任何文字。")
            return CustomRecognition.AnalyzeResult(box=None, detail="No text found in ROI")

        # --- 步骤 4: 筛选并找到最佳目标 ---
        valid_candidates = []
        for reco_detail in ocr_results.filterd_results: 
            try:
                # 使用正则表达式提取所有数字，处理像 '>>>50' 这样的字符串
                num_list = re.findall(r'\d+', reco_detail.text)
                if not num_list:
                    continue  # 如果没有找到数字，则跳过

                # 将找到的数字部分拼接起来并转换为整数
                level = int("".join(num_list))
                
                if level < target_level:
                    valid_candidates.append(reco_detail)
            except (ValueError, TypeError):
                continue  # 忽略无法转换为整数的识别结果
        
        if not valid_candidates:
            logger.info(f"扫描完成，没有找到等级小于 {target_level} 的目标。")
            return CustomRecognition.AnalyzeResult(box=None, detail=f"No target found < {target_level}")

        # 定义一个函数，将 y 坐标“吸附”到标准行
        def snap_y(y_coord):
            if abs(y_coord - 300) < 50:  # 300 附近的都算作 300
                return 300
            if abs(y_coord - 580) < 50:  # 580 附近的都算作 580
                return 580
            return y_coord

        #
        # 使用“吸附”后的 y 值进行排序，实现更稳健的“左上角”查找
        valid_candidates.sort(key=lambda detail: (snap_y(detail.box[1]), detail.box[0]))
        best_candidate = valid_candidates[0]
        
        print(f"成功定位目标: 等级 {best_candidate.text}, 位于 {best_candidate.box}")

        # --- 步骤 5: 返回最终结果 ---
        return CustomRecognition.AnalyzeResult(
            box=best_candidate.box,
            detail=best_candidate.text
        )