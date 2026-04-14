"use client";

import { useConsoleDisplayMode } from "@/components/console-display-mode";
import { PageHeader, Panel } from "@/components/console-ui";

function FlowStep({
  step,
  title,
  description,
  isLast = false,
}: {
  step: number;
  title: string;
  description: string;
  isLast?: boolean;
}) {
  return (
    <div className="flow-step">
      <div className="flow-step-indicator">
        <div className="flow-step-number">{step}</div>
        {!isLast && <div className="flow-step-line" />}
      </div>
      <div className="flow-step-content">
        <div className="flow-step-title">{title}</div>
        <div className="flow-step-desc">{description}</div>
      </div>
    </div>
  );
}

function RuleCard({
  icon,
  title,
  description,
  example,
  tone = "neutral",
}: {
  icon: string;
  title: string;
  description: string;
  example: string;
  tone?: "danger" | "warning" | "neutral";
}) {
  return (
    <div className={`rule-card rule-card--${tone}`}>
      <div className="rule-card-icon">{icon}</div>
      <div className="rule-card-body">
        <div className="rule-card-title">{title}</div>
        <div className="rule-card-desc">{description}</div>
        <div className="rule-card-example">{example}</div>
      </div>
    </div>
  );
}

function ScoreBar({ label, points, color }: { label: string; points: string; color: string }) {
  return (
    <div className="score-bar">
      <div className="score-bar-label">{label}</div>
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ background: color }} />
      </div>
      <div className="score-bar-points">{points}</div>
    </div>
  );
}

export function AlgorithmScreen() {
  const { showAdvanced, setShowAdvanced } = useConsoleDisplayMode();

  if (!showAdvanced) {
    return (
      <div className="algorithm-page">
        <PageHeader
          title="検知アルゴリズムについて"
          description="通常表示では非表示です。必要なときだけ詳細表示に切り替えて確認できます。"
        />
        <Panel title="通常表示では非表示です" description="日常の判定作業に不要な説明をまとめて隠しています。">
          <div className="screen-page">
            <p className="algo-text">
              検知ルールの詳しい説明は、管理者や調査担当が確認するときだけ表示する設計にしています。
            </p>
            <button type="button" className="button button-default" onClick={() => setShowAdvanced(true)}>
              詳細表示に切り替える
            </button>
          </div>
        </Panel>
      </div>
    );
  }

  return (
    <div className="algorithm-page">
      <PageHeader
        title="検知アルゴリズムについて"
        description="不正検知の仕組みをわかりやすく解説します"
      />

      {/* 概要 */}
      <Panel title="概要">
        <p className="algo-text">
          このシステムは、アフィリエイト広告における不正なコンバージョン（成果発生）を自動的に検知します。
          同じIPアドレス・ブラウザの組み合わせからの行動パターンを分析し、
          「量」「タイミング」「クリック水増し」の3つの観点から不審な行動を特定します。
        </p>
        <p className="algo-text">
          機械学習（AI）ではなく、<strong>ルールベース</strong>の検知を採用しています。
          明確なしきい値をもとに判定するため、なぜアラートが出たのかを誰でも理解できます。
        </p>
      </Panel>

      {/* 検知の流れ */}
      <Panel title="検知の流れ">
        <div className="flow-steps">
          <FlowStep
            step={1}
            title="データ取得"
            description="ACS APIからクリックログとコンバージョンログを取得します。"
          />
          <FlowStep
            step={2}
            title="グルーピング"
            description="同じIPアドレス・ブラウザ（ユーザーエージェント）の組み合わせで、1日分のデータをまとめます。"
          />
          <FlowStep
            step={3}
            title="ルール照合"
            description="各グループに対して、以下の検知ルールを適用し、不審なパターンがないか確認します。"
          />
          <FlowStep
            step={4}
            title="リスクスコア算出"
            description="該当したルールの数や種類に応じて、リスクの高さをスコアで表します。"
          />
          <FlowStep
            step={5}
            title="被害額推定"
            description="不正の疑いがあるコンバージョンの件数と広告単価から、被害額を試算します。"
            isLast
          />
        </div>
      </Panel>

      {/* 検知ルール：量の異常 */}
      <Panel title="検知ルール 1：量の異常" description="同じ発信元から短期間に不自然な量の行動が発生していないかを確認します">
        <div className="rule-cards">
          <RuleCard
            icon="&#x1f4ca;"
            title="コンバージョン件数"
            description="同じIPアドレス・ブラウザから1日に5件以上のコンバージョンがあった場合に検知します。"
            example="例：同一のスマートフォンから1日に10件の商品購入が発生"
            tone="warning"
          />
          <RuleCard
            icon="&#x1f4f0;"
            title="メディアの分散"
            description="同じ発信元から2つ以上の異なる広告媒体を経由してコンバージョンしている場合に検知します。"
            example="例：同一端末がサイトA・サイトBの両方から同じ広告に成果を発生させている"
            tone="warning"
          />
          <RuleCard
            icon="&#x1f4e6;"
            title="プログラムの分散"
            description="同じ発信元から2つ以上の異なる広告プログラムでコンバージョンしている場合に検知します。"
            example="例：同一端末が商品Aの広告と商品Bの広告の両方で成果を出している"
            tone="warning"
          />
        </div>
      </Panel>

      {/* 検知ルール：タイミングの異常 */}
      <Panel title="検知ルール 2：タイミングの異常" description="コンバージョンの発生タイミングが不自然でないかを確認します">
        <div className="rule-cards">
          <RuleCard
            icon="&#x26a1;"
            title="バースト検知"
            description="30分以内に3件以上のコンバージョンが集中した場合に検知します。短時間での連続的な成果発生は自動化ツールによる不正の兆候です。"
            example="例：14:00〜14:30の間に5件のコンバージョンが連続発生"
            tone="danger"
          />
          <RuleCard
            icon="&#x23f1;&#xfe0f;"
            title="クリックからコンバージョンまでが異常に速い"
            description="広告をクリックしてからコンバージョンするまでが5秒未満の場合に検知します。通常、人間がページを見て購入するにはもっと時間がかかります。"
            example="例：広告クリックの2秒後に商品購入が完了"
            tone="danger"
          />
          <RuleCard
            icon="&#x1f4c5;"
            title="クリックからコンバージョンまでが異常に遅い"
            description="広告をクリックしてから30日以上経ってからコンバージョンした場合に検知します。不正なCookieの付け替えが疑われます。"
            example="例：45日前のクリックに対して成果が発生"
            tone="warning"
          />
        </div>
      </Panel>

      {/* 検知ルール：クリック水増し */}
      <Panel title="検知ルール 3：クリック水増し（クリックパディング）" description="コンバージョンの前後に不自然なクリックが発生していないかを確認します">
        <div className="rule-cards">
          <RuleCard
            icon="&#x1f5b1;&#xfe0f;"
            title="クリック対コンバージョン比率"
            description="コンバージョン1件あたりのクリック数が2件以上の場合に検知します。成果を水増しするために、余計なクリックを発生させている可能性があります。"
            example="例：コンバージョン3件に対してクリック10件（比率 3.3）"
            tone="warning"
          />
          <RuleCard
            icon="&#x1f4a5;"
            title="コンバージョン前後の余分なクリック"
            description="コンバージョンの前後30分間に10件以上の余分なクリックがある場合に検知します。"
            example="例：購入完了の前後に15件の不審なクリックが発生"
            tone="danger"
          />
          <RuleCard
            icon="&#x1f916;"
            title="非ブラウザクリックの割合"
            description="コンバージョン前後のクリックのうち70%以上がブラウザ以外（ボットやスクリプト）からのアクセスだった場合に検知します。"
            example="例：周辺クリック20件中16件がボットからのアクセス"
            tone="danger"
          />
        </div>
      </Panel>

      {/* フィルタリング */}
      <Panel title="補助フィルタ" description="検知精度を高めるための追加的なフィルタリング機能です">
        <div className="rule-cards">
          <RuleCard
            icon="&#x1f310;"
            title="データセンターIPフィルタ"
            description="AWS、Google Cloud、Azureなどのクラウドサービスのサーバーからのアクセスをフィルタリングできます。通常のユーザーはクラウドサーバーからアクセスしないため、ボットの可能性が高いです。"
            example="対象：AWS、Google Cloud、Azure、Cloudflareなど56種のIPレンジ"
          />
          <RuleCard
            icon="&#x1f50d;"
            title="ブラウザ判定"
            description="アクセス元がChrome、Firefox、Safariなどの一般的なブラウザかどうかを判定します。curl、Python、botなどのプログラムからのアクセスを識別します。"
            example="ブラウザ以外と判定されるもの：bot、crawler、curl、python、wgetなど"
          />
        </div>
      </Panel>

      {/* リスクスコア */}
      <Panel title="リスクスコアの計算方法" description="検知されたルール違反の内容に応じてスコアを加算し、リスクレベルを決定します">
        <div className="algo-scoring">
          <div className="algo-scoring-section">
            <h3 className="algo-subtitle">スコアの加算ルール</h3>
            <div className="score-bars">
              <ScoreBar label="ルール違反1件あたり" points="+25点" color="var(--accent)" />
              <ScoreBar label="バースト検知に該当" points="+30点" color="var(--danger)" />
              <ScoreBar label="異常に速いコンバージョン" points="+25点" color="var(--danger)" />
              <ScoreBar label="メディア/プログラムの分散" points="+15点" color="var(--warning)" />
              <ScoreBar label="クリック水増しに該当" points="+25点" color="var(--warning)" />
              <ScoreBar label="コンバージョン10件以上" points="+40点" color="var(--danger)" />
              <ScoreBar label="コンバージョン5〜9件" points="+20点" color="var(--warning)" />
              <ScoreBar label="コンバージョン3〜4件" points="+10点" color="var(--muted)" />
            </div>
          </div>
          <div className="algo-scoring-section">
            <h3 className="algo-subtitle">リスクレベルの判定</h3>
            <div className="risk-levels">
              <div className="risk-level-row risk-level-row--high">
                <span className="risk-level-badge risk-level-badge--high">高リスク</span>
                <span className="risk-level-condition">スコア 65点以上</span>
                <span className="risk-level-desc">複数の不正兆候あり。優先的に調査が必要です。</span>
              </div>
              <div className="risk-level-row risk-level-row--medium">
                <span className="risk-level-badge risk-level-badge--medium">中リスク</span>
                <span className="risk-level-condition">スコア 30〜64点</span>
                <span className="risk-level-desc">一部の不正兆候あり。確認をおすすめします。</span>
              </div>
              <div className="risk-level-row risk-level-row--low">
                <span className="risk-level-badge risk-level-badge--low">低リスク</span>
                <span className="risk-level-condition">スコア 30点未満</span>
                <span className="risk-level-desc">軽微な兆候のみ。経過観察で問題ありません。</span>
              </div>
            </div>
          </div>
        </div>
      </Panel>

      {/* 被害額推定 */}
      <Panel title="被害額の推定方法" description="不正の疑いがあるコンバージョンによる金銭的な被害を試算します">
        <p className="algo-text">
          被害推定額は、不正と疑われるコンバージョンの件数に広告プログラムの単価を掛けて算出します。
        </p>
        <div className="damage-formula">
          <div className="damage-formula-box">
            <span className="damage-formula-item">不正疑いCV件数</span>
            <span className="damage-formula-op">&times;</span>
            <span className="damage-formula-item">広告単価（円）</span>
            <span className="damage-formula-op">=</span>
            <span className="damage-formula-item damage-formula-result">被害推定額</span>
          </div>
          <p className="algo-text-small">
            広告単価が不明な場合は、デフォルト値（3,000円）を使用します。
            プログラムごとに単価が異なる場合は、それぞれの単価で個別に計算した合計値になります。
          </p>
        </div>
      </Panel>

      {/* 注意事項 */}
      <Panel title="ご注意">
        <div className="algo-notice">
          <p className="algo-text">
            本システムの検知結果はあくまで「疑い」であり、すべてのアラートが実際の不正であるとは限りません。
            アラートの内容を確認した上で、「不正」「ホワイト（正常）」「調査中」のいずれかに分類してください。
          </p>
          <p className="algo-text">
            しきい値やルールは設定により変更可能です。運用状況に応じて調整することで、検知精度を向上させることができます。
          </p>
        </div>
      </Panel>
    </div>
  );
}
