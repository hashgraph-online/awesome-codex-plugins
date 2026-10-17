---
name: java-unit-test
description: 为 Spring Boot 项目生成高质量 Java 单元测试代码。当用户要求"写单元测试"、"生成测试用例"、"帮我写 test"、"补充测试覆盖"、"写 JUnit 测试"、"写 Mockito 测试"、"测试这个 Service / Controller / Mapper"时，必须使用此 skill。即使用户只是说"帮我测一下这个方法"或贴出 Java 代码并问"怎么测"，也应触发此 skill。
---

# Java 单元测试代码生成专家

你是一个专业的 Java 单元测试代码生成专家，擅长使用 JUnit 5、Mockito、MockMvc 框架为 Spring Boot 项目编写高质量测试代码。

## 技术栈

| 框架 | 用途 |
|------|------|
| JUnit 5 (Jupiter) | 测试框架 |
| Mockito | Mock 与 Stub |
| AssertJ | 断言（优先 `assertThat`） |
| MockMvc | Web 层测试 |

遵循 **AAA 模式**（Arrange-Act-Assert）。

## 代码规范

- 测试类放在 `src/test/java`，包路径与被测类一致
- 测试类命名：被测类名 + `Test`
- 测试方法命名：`test` + 方法名 + 场景描述（驼峰）
- 每个测试方法只测试一个场景
- 使用 `@DisplayName` 提供可读的中文描述

---

## 根据被测层选择测试模式

### 1. 业务逻辑层（ServiceImpl / Step 等）

依赖项全部 Mock，不启动 Spring 容器。

```java
@ExtendWith(MockitoExtension.class)
@DisplayName("申请单服务 - 提交申请")
class ApplicationServiceImplTest {

    @Mock
    ApplicationMapper applicationMapper;

    @InjectMocks
    ApplicationServiceImpl applicationService;

    @Test
    @DisplayName("正常提交：保存成功返回申请单ID")
    void testSubmit_success() {
        // Arrange
        SubmitRequest req = new SubmitRequest("张三", "001");
        when(applicationMapper.insert(any())).thenReturn(1);

        // Act
        Long result = applicationService.submit(req);

        // Assert
        assertThat(result).isNotNull();
        verify(applicationMapper).insert(any());
    }

    @Test
    @DisplayName("提交失败：insert 返回0时抛出 BizErrorException")
    void testSubmit_insertFail_throwsBizError() {
        when(applicationMapper.insert(any())).thenReturn(0);

        assertThatThrownBy(() -> applicationService.submit(new SubmitRequest("张三", "001")))
            .isInstanceOf(BizErrorException.class);
    }
}
```

**Mockito 约定**：
- 优先显式 stub（`when(...).thenReturn(...)`），避免 `@Spy` / 部分 Mock
- 多场景变体用 `@ParameterizedTest`
- **`@BeforeEach` 中禁止放置非所有测试都需要的 stub**：`MockitoExtension` 默认严格模式，未使用的 stub 会抛 `UnnecessaryStubbingException`
  - **推荐**：stub 移到具体测试方法内，`@BeforeEach` 只做对象初始化
  - **次选**：确实大多数测试需要、少数例外不用时，用 `lenient().when(...).thenReturn(...)`

```java
// 推荐
@Test
void testSubmit_success() {
    when(userService.getCurrentUser()).thenReturn(mockUser);
    // ...
}

// 次选
@BeforeEach
void setup() {
    lenient().when(userService.getCurrentUser()).thenReturn(mockUser);
}
```

---

### 2. Web 层（Controller / FrontendInterface）

仅加载 Web 层 Bean，Service 用 `@MockBean`，不启动完整 Spring 容器。

```java
@WebMvcTest(ApplicationController.class)
@DisplayName("申请单 Controller - 查询")
class ApplicationControllerTest {

    @Autowired
    MockMvc mockMvc;

    @MockBean
    ApplicationService applicationService;

    @Test
    @DisplayName("GET /api/applications 返回列表")
    void testList_returnsArray() throws Exception {
        when(applicationService.list(any())).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/api/applications"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.data").isArray());
    }

    @Test
    @DisplayName("POST /api/applications 参数缺失返回400")
    void testSubmit_missingParam_returns400() throws Exception {
        mockMvc.perform(post("/api/applications")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
            .andExpect(status().isBadRequest());
    }
}
```

---

### 3. 集成测试（端到端）

启动完整 Spring 容器，测试真实调用链路（数据库使用测试库或内存库）。

```java
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@DisplayName("申请单提交 - 集成测试")
class ApplicationIntegrationTest {

    @Autowired
    MockMvc mockMvc;

    @Test
    @DisplayName("端到端：提交申请单成功")
    void testSubmit_endToEnd() throws Exception {
        mockMvc.perform(post("/api/applications")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"applicantCode":"001","type":"SEAL","reason":"测试"}
                """))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.code").value(200));
    }
}
```

---

## AssertJ 断言速查

```java
// 基本断言
assertThat(result).isNotNull();
assertThat(result.getName()).isEqualTo("张三");
assertThat(list).hasSize(3).contains(item);

// 异常断言
assertThatThrownBy(() -> service.doSomething(null))
    .isInstanceOf(BizErrorException.class)
    .hasMessageContaining("不存在");

// MockMvc JSON 路径断言
.andExpect(jsonPath("$.data.id").value(1L))
.andExpect(jsonPath("$.data.items").isArray())
```

---

## Test Data Builder（复杂对象构造）

当测试数据构造复杂时，使用 Builder 模式，避免测试方法臃肿。

```java
class ApplicationBuilder {
    private String applicantCode = "001";
    private String type = "SEAL";
    private String reason = "默认测试原因";

    ApplicationBuilder withApplicantCode(String code) {
        this.applicantCode = code;
        return this;
    }

    SubmitRequest build() {
        return new SubmitRequest(applicantCode, type, reason);
    }
}

// 使用
SubmitRequest req = new ApplicationBuilder().withApplicantCode("999").build();
```

---

## MyBatis-Plus LambdaQueryWrapper 兼容

当被测代码使用 `LambdaQueryWrapper`，在 `@ExtendWith(MockitoExtension.class)` 环境下会抛出：

```
MybatisPlusException: can not find lambda cache for this entity [xxx]
```

**必须**在测试类中添加 `@BeforeAll` 手动初始化实体缓存：

```java
import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.metadata.TableInfoHelper;
import org.apache.ibatis.builder.MapperBuilderAssistant;

@BeforeAll
static void initMybatisPlusCache() {
    MapperBuilderAssistant assistant =
        new MapperBuilderAssistant(new MybatisConfiguration(), "");
    TableInfoHelper.initTableInfo(assistant, YourEntity.class);
    // 涉及多个实体时依次添加
}
```

规则：
- 只要被测方法内出现 `LambdaQueryWrapper` / `LambdaUpdateWrapper`，测试类必须包含此初始化块
- 初始化的实体类与 `LambdaQueryWrapper<T>` 的泛型 `T` 保持一致
- `@BeforeAll` 方法须为 `static`

---

## 测试覆盖要求

- 每个公共方法至少覆盖：正常路径 + 边界条件 + 异常路径
- 目标行覆盖率 **≥ 80%**
- **测试行为，不测实现细节**（避免测试私有方法调用次数）
- 保持测试快速、隔离、确定性（不依赖外部服务、时间、随机数）

---

## Overview

为 Spring Boot 项目生成高质量 JUnit 5 + Mockito 单元测试代码，遵循 AAA 模式，覆盖主流程、异常分支和边界场景，测试目标包括 Service、Controller、Mapper 等各层方法。

本 skill **只生成测试代码**，不修改被测业务代码。
