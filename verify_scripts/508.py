"""
POI验证函数
用于验证POI ID是否符合给定的验证条件
"""
import sys
import os
from typing import List, Dict

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from tools.amap_tools import (
    maps_search_detail,
    maps_distance,
    maps_driving_by_coordinates,
    maps_geo,
    maps_walking_by_coordinates,
    maps_text_search,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search

"""
根据给定的验证方法验证POI是否符合要求。
输入：B03820Q18F
输出：True

验证方法：
🔍 验证方法 (verification_method):
1) 调用 maps_around_search(location="110.351225,20.073076", radius="5000", keywords="青年旅舍")，验证返回结果中包含 target_poi_id=B03820Q18F，证明其在5km范围内且为青年旅舍。
2) 调用 maps_search_detail(id="B03820Q18F")，读取 biz_ext.rating，验证评分 >= 4.6（该POI rating=4.6）。并获取其坐标 location=110.362121,20.062489 供后续路线计算。
3) 调用 maps_walking_by_coordinates(origin="110.351225,20.073076", destination="110.362121,20.062489")，验证 total_duration_seconds <= 1500（25分钟）。
4) 调用 maps_bicycling_by_coordinates(origin="110.351225,20.073076", destination="110.362121,20.062489")，验证 total_duration_seconds <= 720（12分钟）。
5) 调用 maps_driving_by_coordinates(origin="110.351225,20.073076", destination="110.362121,20.062489")，验证 total_duration_seconds <= 480（8分钟）。
"""
def verify_poi(
    target_poi_id: str = "B03820Q18F",
    user_coordinates: str = "110.351225,20.073076",
    search_radius: str = "5000",
    search_keywords: str = "青年旅舍",
    min_rating: float = 4.6,
    max_walking_duration: int = 1500,
    max_bicycling_duration: int = 720,
    max_driving_duration: int = 480
) -> bool:
    """
    验证POI ID是否符合给定的验证条件
    
    Args:
        target_poi_id: 目标POI ID，默认值为 "B03820Q18F"
        user_coordinates: 用户坐标，格式为"经度,纬度"，默认值为 "110.351225,20.073076"
        search_radius: 搜索半径（米），默认值为 "5000"
        search_keywords: 搜索关键词，默认值为 "青年旅舍"
        min_rating: 最小评分，默认值为 4.6
        max_walking_duration: 最大步行时长（秒），默认值为 1500（25分钟）
        max_bicycling_duration: 最大骑行时长（秒），默认值为 720（12分钟）
        max_driving_duration: 最大驾车时长（秒），默认值为 480（8分钟）
    
    Returns:
        str: 验证结果，可能的值有："满足"、"部分满足"、"不满足"
    """
    print("=" * 80)
    print(f"开始验证POI ID: {target_poi_id}")
    print("=" * 80)
    
    # 记录验证结果
    passed_checks = []
    failed_checks = []
    
    # 步骤1: 调用 maps_around_search 验证返回结果中包含 target_poi_id
    print("\n【步骤1】调用 maps_around_search(location=\"{}\", radius=\"{}\", keywords=\"{}\")，验证返回结果中包含 target_poi_id={}".format(
        user_coordinates, search_radius, search_keywords, target_poi_id))
    print("-" * 80)
    around_search_result = maps_around_search(location=user_coordinates, radius=search_radius, keywords=search_keywords)
    if around_search_result.error:
        print(f"❌ 步骤1失败: {around_search_result.error}")
        failed_checks.append("步骤1: 周边搜索失败")
    else:
        if not around_search_result.pois:
            print(f"❌ 步骤1失败: 未找到任何POI结果")
            failed_checks.append("步骤1: 未找到任何POI结果")
        else:
            # 检查返回结果中是否包含 target_poi_id
            found_target_poi = False
            for poi in around_search_result.pois:
                if poi.id == target_poi_id:
                    found_target_poi = True
                    print(f"✅ 步骤1通过: 在搜索结果中找到目标POI ID {target_poi_id}")
                    print(f"   POI名称: {poi.name or '未知'}")
                    passed_checks.append("步骤1: 在5km范围内且为青年旅舍")
                    break
            
            if not found_target_poi:
                print(f"❌ 步骤1失败: 搜索结果中未找到目标POI ID {target_poi_id}")
                print(f"   找到 {len(around_search_result.pois)} 个其他POI结果")
                failed_checks.append("步骤1: 搜索结果中未包含目标POI ID")
    
    # 步骤2: 调用 maps_search_detail 获取POI的rating和location
    print("\n【步骤2】调用 maps_search_detail(id=\"{}\")，读取 biz_ext.rating，验证评分 >= {}，并获取坐标 location".format(
        target_poi_id, min_rating))
    print("-" * 80)
    poi_detail = maps_search_detail(target_poi_id)
    if poi_detail.error:
        print(f"❌ 步骤2失败: {poi_detail.error}")
        print("\n" + "=" * 80)
        print("最终验证结果: 不满足（无法获取POI信息）")
        print("=" * 80)
        return "不满足"
    
    if not poi_detail.location:
        print(f"❌ 步骤2失败: POI详情中未找到坐标信息")
        print("\n" + "=" * 80)
        print("最终验证结果: 不满足（无法获取POI坐标）")
        print("=" * 80)
        return "不满足"
    
    poi_location = poi_detail.location
    print(f"✅ 获取到POI坐标: {poi_location}")
    print(f"   POI名称: {poi_detail.name or '未知'}")
    
    # 验证评分
    if not poi_detail.biz_ext:
        print(f"❌ 步骤2失败: POI详情中未找到biz_ext信息")
        failed_checks.append("步骤2: 未找到biz_ext信息")
    else:
        rating = poi_detail.biz_ext.get("rating")
        if rating is None:
            print(f"❌ 步骤2失败: biz_ext中未找到rating字段")
            failed_checks.append("步骤2: 未找到rating字段")
        else:
            try:
                rating_float = float(rating)
                if rating_float >= min_rating:
                    print(f"✅ 步骤2通过: 评分为 {rating_float} >= {min_rating}")
                    passed_checks.append("步骤2: 评分 >= {}".format(min_rating))
                else:
                    print(f"❌ 步骤2失败: 评分为 {rating_float} < {min_rating}")
                    failed_checks.append("步骤2: 评分 {} < {}".format(rating_float, min_rating))
            except (ValueError, TypeError):
                print(f"❌ 步骤2失败: rating值无法转换为数字: {rating}")
                failed_checks.append("步骤2: rating值无法转换为数字")
    
    # 步骤3: 验证步行时长 <= 1500秒（25分钟）
    print("\n【步骤3】调用 maps_walking_by_coordinates(origin=\"{}\", destination=\"{}\")，验证 total_duration_seconds <= {}（{}分钟）".format(
        user_coordinates, poi_location, max_walking_duration, max_walking_duration // 60))
    print("-" * 80)
    walking_result = maps_walking_by_coordinates(origin=user_coordinates, destination=poi_location)
    if walking_result.error:
        print(f"❌ 步骤3失败: {walking_result.error}")
        failed_checks.append("步骤3: 步行路线验证失败")
    else:
        if walking_result.total_duration_seconds is None:
            print(f"❌ 步骤3失败: 无法获取步行时长")
            failed_checks.append("步骤3: 无法获取步行时长")
        else:
            walking_duration = walking_result.total_duration_seconds
            if walking_duration <= max_walking_duration:
                print(f"✅ 步骤3通过: 步行时长为 {walking_duration}秒 <= {max_walking_duration}秒（{max_walking_duration // 60}分钟）")
                passed_checks.append("步骤3: 步行时长 <= {}秒".format(max_walking_duration))
            else:
                print(f"❌ 步骤3失败: 步行时长为 {walking_duration}秒 > {max_walking_duration}秒（{max_walking_duration // 60}分钟）")
                failed_checks.append("步骤3: 步行时长 {}秒 > {}秒".format(walking_duration, max_walking_duration))
    
    # 步骤4: 验证骑行时长 <= 720秒（12分钟）
    print("\n【步骤4】调用 maps_bicycling_by_coordinates(origin=\"{}\", destination=\"{}\")，验证 total_duration_seconds <= {}（{}分钟）".format(
        user_coordinates, poi_location, max_bicycling_duration, max_bicycling_duration // 60))
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(origin=user_coordinates, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 步骤4失败: {bicycling_result.error}")
        failed_checks.append("步骤4: 骑行路线验证失败")
    else:
        if bicycling_result.total_duration_seconds is None:
            print(f"❌ 步骤4失败: 无法获取骑行时长")
            failed_checks.append("步骤4: 无法获取骑行时长")
        else:
            bicycling_duration = bicycling_result.total_duration_seconds
            if bicycling_duration <= max_bicycling_duration:
                print(f"✅ 步骤4通过: 骑行时长为 {bicycling_duration}秒 <= {max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
                passed_checks.append("步骤4: 骑行时长 <= {}秒".format(max_bicycling_duration))
            else:
                print(f"❌ 步骤4失败: 骑行时长为 {bicycling_duration}秒 > {max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
                failed_checks.append("步骤4: 骑行时长 {}秒 > {}秒".format(bicycling_duration, max_bicycling_duration))
    
    # 步骤5: 验证驾车时长 <= 480秒（8分钟）
    print("\n【步骤5】调用 maps_driving_by_coordinates(origin=\"{}\", destination=\"{}\")，验证 total_duration_seconds <= {}（{}分钟）".format(
        user_coordinates, poi_location, max_driving_duration, max_driving_duration // 60))
    print("-" * 80)
    driving_result = maps_driving_by_coordinates(origin=user_coordinates, destination=poi_location)
    if driving_result.error:
        print(f"❌ 步骤5失败: {driving_result.error}")
        failed_checks.append("步骤5: 驾车路线验证失败")
    else:
        if driving_result.total_duration_seconds is None:
            print(f"❌ 步骤5失败: 无法获取驾车时长")
            failed_checks.append("步骤5: 无法获取驾车时长")
        else:
            driving_duration = driving_result.total_duration_seconds
            if driving_duration <= max_driving_duration:
                print(f"✅ 步骤5通过: 驾车时长为 {driving_duration}秒 <= {max_driving_duration}秒（{max_driving_duration // 60}分钟）")
                passed_checks.append("步骤5: 驾车时长 <= {}秒".format(max_driving_duration))
            else:
                print(f"❌ 步骤5失败: 驾车时长为 {driving_duration}秒 > {max_driving_duration}秒（{max_driving_duration // 60}分钟）")
                failed_checks.append("步骤5: 驾车时长 {}秒 > {}秒".format(driving_duration, max_driving_duration))
    
    # 输出验证结果汇总
    print("\n" + "=" * 80)
    print("验证结果汇总")
    print("=" * 80)
    print(f"\n通过的验证 ({len(passed_checks)}/{len(passed_checks) + len(failed_checks)}):")
    for check in passed_checks:
        print(f"  ✅ {check}")
    
    if failed_checks:
        print(f"\n未通过的验证 ({len(failed_checks)}/{len(passed_checks) + len(failed_checks)}):")
        for check in failed_checks:
            print(f"  ❌ {check}")
    
    # 判断最终结果
    total_checks = len(passed_checks) + len(failed_checks)
    if len(failed_checks) == 0:
        result = "满足"
    elif len(passed_checks) == 0:
        result = "不满足"
    else:
        result = "部分满足"
    
    print("\n" + "=" * 80)
    print(f"最终验证结果: {result}")
    print("=" * 80)
    if result == "满足":
        return True
    else:
        return False


def main():
    verify_poi("B03820Q18F")  


if __name__ == "__main__":
    main()
