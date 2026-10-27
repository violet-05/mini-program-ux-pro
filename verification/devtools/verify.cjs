#!/usr/bin/env node
'use strict'

/**
 * MPUX Pro 微信开发者工具运行时验收脚本。
 *
 * 前置：
 * - 微信开发者工具安全设置中开启服务端口 / CLI HTTP 调用；
 * - 在 verification/devtools 运行 npm install；
 * - 传入 cliPath（或设置 WECHAT_DEVTOOLS_CLI）。
 *
 * 本脚本只截取开发者工具模拟器，不代表真机；验证后仅断开连接，不关闭 IDE。
 */

const fs = require('fs')
const path = require('path')
const { spawnSync } = require('child_process')
const automator = require('miniprogram-automator')

const REPO_ROOT = path.resolve(__dirname, '..', '..')
const DEFAULT_PROJECT = path.resolve(__dirname, '..')

function parseArgs(argv) {
  const args = {}
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index]
    if (!token.startsWith('--')) continue
    const key = token.slice(2)
    const next = argv[index + 1]
    if (!next || next.startsWith('--')) {
      args[key] = true
    } else {
      args[key] = next
      index += 1
    }
  }
  return args
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function numberFromSize(value) {
  return Number.parseFloat(String(value || '0').replace(/[^\d.]/g, '')) || 0
}

function rel(file) {
  return path.relative(REPO_ROOT, file).split(path.sep).join('/')
}

class VerificationFailure extends Error {}

function assert(condition, message, detail) {
  if (!condition) {
    const suffix = detail === undefined ? '' : `：${JSON.stringify(detail)}`
    throw new VerificationFailure(`${message}${suffix}`)
  }
}

async function connectAutomation(port, timeout = 25000) {
  const started = Date.now()
  let lastError = null
  while (Date.now() - started < timeout) {
    try {
      return await automator.connect({ wsEndpoint: `ws://127.0.0.1:${port}` })
    } catch (error) {
      lastError = error
      await sleep(700)
    }
  }
  throw new VerificationFailure(
    `连接自动化端口 ${port} 超时：${lastError ? lastError.message : 'unknown'}`
  )
}

function startDevToolsAutomation(cliPath, projectPath, port) {
  const commandLine = `"${cliPath}" auto --project "${projectPath}" --auto-port ${port} --trust-project`
  const result = spawnSync(commandLine, {
    shell: true,
    encoding: 'utf8',
    timeout: 90000
  })
  const output = `${result.stdout || ''}${result.stderr || ''}`.trim()
  if (result.error) {
    throw new VerificationFailure(`启动开发者工具自动化失败：${result.error.message}`)
  }
  if (result.status !== 0) {
    throw new VerificationFailure(
      `启动开发者工具自动化失败（exit ${result.status}）：${output.slice(-2500)}`
    )
  }
  return output
}

async function waitForPath(miniProgram, expected, timeout = 7000) {
  const started = Date.now()
  while (Date.now() - started < timeout) {
    const page = await miniProgram.currentPage()
    if (page && page.path && page.path.includes(expected)) return page
    await sleep(180)
  }
  const page = await miniProgram.currentPage()
  throw new VerificationFailure(
    `等待页面 ${expected} 超时，当前页面：${page ? page.path : 'unknown'}`
  )
}

async function screenshot(miniProgram, artifacts, name) {
  const file = path.join(artifacts, name)
  if (fs.existsSync(file)) fs.unlinkSync(file)
  const attempts = 2
  let lastError = null
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      await miniProgram.screenshot({ path: file })
      const stat = fs.statSync(file)
      assert(stat.size > 1000, `截图文件为空或过小：${name}`, stat.size)
      return { name, path: rel(file), bytes: stat.size, attempts: attempt }
    } catch (error) {
      lastError = error
      if (attempt < attempts) {
        console.log(`RETRY 截图 ${name}：${error.message}`)
        await sleep(1200)
      }
    }
  }
  throw lastError
}

async function elementSize(page, selector) {
  const element = await page.$(selector)
  assert(element, `找不到元素 ${selector}`)
  return { element, size: await element.size() }
}

async function tap(page, selector) {
  const { element, size } = await elementSize(page, selector)
  await element.tap()
  return size
}

async function main() {
  const args = parseArgs(process.argv.slice(2))
  const projectPath = path.resolve(args.project || DEFAULT_PROJECT)
  const artifacts = path.resolve(
    args.artifacts || path.join(__dirname, '..', 'artifacts')
  )
  const cliPath = args.cli || process.env.WECHAT_DEVTOOLS_CLI
  const port = Number.parseInt(args.port || '9420', 10)
  fs.mkdirSync(artifacts, { recursive: true })

  if (!cliPath) {
    throw new VerificationFailure(
      '缺少 --cli，或设置 WECHAT_DEVTOOLS_CLI 为 cli.bat 的绝对路径。'
    )
  }
  if (!fs.existsSync(cliPath)) {
    throw new VerificationFailure(`CLI 不存在：${cliPath}`)
  }

  const report = {
    schema_version: '1.0.0',
    runner: 'verification/devtools/verify.cjs',
    automator_version: require('miniprogram-automator/package.json').version,
    started_at: new Date().toISOString(),
    environment: {
      kind: 'wechat-devtools-simulator',
      cli_path: cliPath,
      project_path: projectPath,
      automation_port: port,
      note: '仅开发者工具模拟器，不是真机；截图不支持客户端真机。'
    },
    checks: [],
    screenshots: [],
    console: [],
    exceptions: [],
    status: 'running'
  }

  let miniProgram = null
  let failure = null
  const check = (name, passed, detail) => {
    report.checks.push({ name, passed: Boolean(passed), detail: detail || null })
    console.log(`${passed ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`)
    if (!passed) throw new VerificationFailure(`检查失败：${name}`)
  }

  try {
    report.connection_mode = 'connect-after-cli-auto'
    try {
      miniProgram = await connectAutomation(port, 1200)
      report.devtools_cli_output = '已存在可连接的自动化端口，直接复用。'
    } catch (initialError) {
      report.devtools_cli_output = startDevToolsAutomation(cliPath, projectPath, port)
      miniProgram = await connectAutomation(port, 30000)
    }

    miniProgram.on('console', (event) => {
      if (report.console.length < 200) report.console.push(event)
    })
    miniProgram.on('exception', (event) => {
      if (report.exceptions.length < 100) report.exceptions.push(event)
    })

    await sleep(1200)
    const systemInfo = await miniProgram.systemInfo()
    report.system_info = {
      SDKVersion: systemInfo.SDKVersion,
      windowWidth: systemInfo.windowWidth,
      windowHeight: systemInfo.windowHeight,
      screenWidth: systemInfo.screenWidth,
      screenHeight: systemInfo.screenHeight,
      statusBarHeight: systemInfo.statusBarHeight,
      safeArea: systemInfo.safeArea || null,
      platform: systemInfo.platform
    }
    check('开发者工具连接并读取系统信息', Boolean(systemInfo.windowWidth), systemInfo.SDKVersion)

    let home = await miniProgram.reLaunch('/pages/home/index')
    await home.waitFor(900)
    let homeData = await home.data()
    check('首页加载完成且进入正常状态', homeData.loading === false && homeData.demoState === 'normal')

    const hero = await home.$('.display')
    assert(hero, '首页缺少主标题')
    report.checks.push({
      name: '首页主标题可读取',
      passed: true,
      detail: await hero.text()
    })
    report.screenshots.push(await screenshot(miniProgram, artifacts, '01-home-normal.png'))

    const openSize = await tap(home, '.open-player')
    check(
      '继续播放按钮触摸尺寸 >= 44px',
      numberFromSize(openSize.width) >= 44 && numberFromSize(openSize.height) >= 44,
      openSize
    )

    const player = await waitForPath(miniProgram, 'pages/player/index')
    await player.waitFor(700)
    const playerData = await player.data()
    check(
      '自定义导航获取状态栏/胶囊信息',
      playerData.statusBarHeight > 0 &&
        playerData.navContentHeight >= 44 &&
        playerData.capsuleReserve > 0,
      {
        statusBarHeight: playerData.statusBarHeight,
        navContentHeight: playerData.navContentHeight,
        capsuleReserve: playerData.capsuleReserve
      }
    )
    check('播放器初始为暂停', playerData.isPlaying === false)
    check('播放器歌词初始展开', playerData.showLyrics === true)
    report.screenshots.push(await screenshot(miniProgram, artifacts, '02-player-initial.png'))

    await tap(player, '.lyrics-toggle')
    await player.waitFor(220)
    check('歌词可以收起', (await player.data()).showLyrics === false)
    await tap(player, '.lyrics-toggle')
    await player.waitFor(220)
    check('歌词可以重新展开', (await player.data()).showLyrics === true)

    const playSize = await tap(player, '.play-button')
    await player.waitFor(320)
    const playingData = await player.data()
    check('点击播放后状态切换为播放', playingData.isPlaying === true)
    check(
      '播放按钮触摸尺寸 >= 44px',
      numberFromSize(playSize.width) >= 44 && numberFromSize(playSize.height) >= 44,
      playSize
    )
    report.screenshots.push(await screenshot(miniProgram, artifacts, '03-player-playing.png'))

    await tap(player, '.favorite-button')
    await player.waitFor(220)
    const favoriteData = await player.data()
    check('收藏按钮状态切换', favoriteData.isFavorite === true)

    await tap(player, '.queue-button')
    await player.waitFor(220)
    const queueData = await player.data()
    check('打开播放队列', queueData.showQueue === true)
    report.screenshots.push(await screenshot(miniProgram, artifacts, '04-player-queue.png'))

    await tap(player, '.queue-close')
    await player.waitFor(220)
    check('关闭播放队列', (await player.data()).showQueue === false)

    const navSize = await tap(player, '.nav-back')
    check(
      '自定义返回触摸尺寸 >= 44px',
      numberFromSize(navSize.width) >= 44 && numberFromSize(navSize.height) >= 44,
      navSize
    )
    home = await waitForPath(miniProgram, 'pages/home/index')
    await home.waitFor(500)
    check('自定义返回回到首页', home.path.includes('pages/home/index'))

    home = await miniProgram.reLaunch('/pages/home/index?demo=error')
    await home.waitFor(500)
    const errorData = await home.data()
    check('错误状态可进入且有重试入口', errorData.demoState === 'error')
    assert(await home.$('.retry-button'), '错误状态缺少重试按钮')
    report.screenshots.push(await screenshot(miniProgram, artifacts, '05-home-error.png'))

    await tap(home, '.retry-button')
    await home.waitFor(800)
    const recoveredData = await home.data()
    check(
      '错误状态重试后恢复推荐',
      recoveredData.demoState === 'normal' && recoveredData.loading === false
    )
    report.screenshots.push(await screenshot(miniProgram, artifacts, '09-home-recovered.png'))

    home = await miniProgram.reLaunch('/pages/home/index?demo=empty')
    await home.waitFor(500)
    const emptyData = await home.data()
    check('空状态可进入且有下一步', emptyData.demoState === 'empty')
    const resetButton = await home.$('.reset-button')
    assert(resetButton, '空状态缺少回到推荐按钮')
    report.screenshots.push(await screenshot(miniProgram, artifacts, '06-home-empty.png'))
    await resetButton.tap()
    await home.waitFor(350)
    check('空状态可以回到推荐', (await home.data()).demoState === 'normal')

    home = await miniProgram.reLaunch('/pages/home/index')
    await home.waitFor(650)
    await home.setData({ loading: true, demoState: 'normal' })
    await home.waitFor(180)
    check('加载骨架状态可渲染', (await home.data()).loading === true)
    report.screenshots.push(await screenshot(miniProgram, artifacts, '07-home-loading.png'))
    await home.setData({ loading: false })

    const profile = await miniProgram.switchTab('/pages/profile/index')
    await profile.waitFor(1200)
    check('TabBar 切换至个人中心', profile.path.includes('pages/profile/index'))
    report.screenshots.push(await screenshot(miniProgram, artifacts, '08-profile.png'))

    await miniProgram.reLaunch('/pages/home/index')
    await sleep(400)

    const errorLogs = report.console.filter((entry) => {
      const type = entry && (entry.type || entry.level)
      return type === 'error'
    })
    report.console_error_count = errorLogs.length
    check(
      '运行期间无 console.error',
      errorLogs.length === 0,
      errorLogs.slice(0, 3)
    )
    check(
      '运行期间无未捕获异常',
      report.exceptions.length === 0,
      report.exceptions.slice(0, 2)
    )
    report.status = 'passed'
  } catch (error) {
    failure = error
    report.status = 'failed'
    report.error = {
      name: error.name,
      message: error.message,
      stack: error.stack
    }
    try {
      if (miniProgram) {
        report.failure_screenshot = await screenshot(
          miniProgram,
          artifacts,
          '99-failure.png'
        )
      }
    } catch (screenshotError) {
      report.failure_screenshot_error = screenshotError.message
    }
  } finally {
    if (miniProgram) {
      try {
        await miniProgram.disconnect()
      } catch (disconnectError) {
        report.disconnect_error = disconnectError.message
      }
    }
    report.finished_at = new Date().toISOString()
    const resultsPath = path.join(artifacts, 'results.json')
    fs.writeFileSync(resultsPath, JSON.stringify(report, null, 2) + '\n', 'utf8')
    console.log(
      JSON.stringify(
        {
          status: report.status,
          checks: report.checks.length,
          passed: report.checks.filter((item) => item.passed).length,
          screenshots: report.screenshots.map((item) => item.path),
          results: rel(resultsPath),
          error: failure ? failure.message : null
        },
        null,
        2
      )
    )
    console.log('开发者工具保持打开，自动化连接已断开。')
    if (failure) process.exitCode = 1
  }
}

main().catch((error) => {
  console.error('MPUX DevTools verification failed before launch:')
  console.error(error && error.stack ? error.stack : error)
  process.exitCode = 1
})