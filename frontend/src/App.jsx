import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BookOpenText,
  MapPin,
  MapTrifold,
  Plus,
} from "@phosphor-icons/react";
import CanalMap from "./CanalMap";
import { MAP_CHARACTERS } from "./mapData";
import { detectSpot, SPOTS } from "./spots";
import { SpotModal, SpotPanel } from "./SpotView";

const FALLBACK_CHARACTERS = [
  {
    id: "su-shi-xuzhou",
    name: "苏轼",
    alias: "苏东坡",
    city: "徐州",
    dynasty: "北宋",
    short_intro: "以诗心观水脉，以民生论徐州。",
    active_time: "熙宁十年（1077年），任徐州知州时",
    portrait_mark: "东",
    biography: [
      { year: 1077, title: "徐州抗洪", description: "黄河决口逼近徐州，苏轼率军民筑堤守城。" },
      { year: 1078, title: "建黄楼", description: "洪水退后建黄楼，以纪念徐州军民抗洪。" },
    ],
    opening_lines: {
      tourism: "你好，我是苏轼。到了徐州，咱们别急着赶景点，先从黄楼边儿走起。我一边陪你看水，一边给你讲讲这座城。你想轻松逛，还是想多听点治水的往事？",
      story: "你来得正好，城外的水势还在涨。别站着了，先跟我到堤上看看。你愿意帮我清点人手，还是先去问问哪一段堤最危险？",
    },
  },
  {
    id: "chen-xuan-huaian",
    name: "陈瑄",
    alias: "平江伯",
    city: "淮安",
    dynasty: "明代",
    short_intro: "一闸一尺皆有定数，南船北运自此通漕。",
    active_time: "永乐十三年（1415年）开凿清江浦前后",
    portrait_mark: "漕",
    biography: [
      { year: 1415, title: "开凿清江浦", description: "主持开河并设置多座闸门，改善淮安段通航。" },
      { title: "完善漕运体系", description: "整治河道、改良浅船并组织沿线运输。" },
    ],
    opening_lines: {
      tourism: "我是陈瑄。咱们从清江浦出发，先看水闸和河道怎么配合，再沿里运河慢慢走。你更想听漕运的故事，还是想要一条好走的路线？",
      story: "你来得正好，闸坝那边有点渗水。咱们先去现场，你帮我看土质和水位，咱们再决定怎么做。",
    },
  },
  {
    id: "zhang-boxing-suzhou",
    name: "张伯行",
    alias: "恕斋",
    city: "苏州",
    dynasty: "清代",
    short_intro: "治河先正其心，一丝一粒皆关民生。",
    active_time: "康熙年间任江苏巡抚时",
    portrait_mark: "廉",
    biography: [
      { title: "任江苏巡抚", description: "整饬吏治、赈济百姓并关注江苏水利。" },
      { title: "总结治水经验", description: "著有《居济一得》，记录河务实践认识。" },
    ],
    opening_lines: {
      tourism: "我是张伯行。苏州的河道，得慢慢走、慢慢看。咱们先从巡抚衙门旧址说起，再去看水城里那些和日常生活连在一起的河。你想走得轻松些，还是多听些治河的事？",
      story: "雨下了几日，河堤那边传来消息，物料账目也有些不对。你随我去一趟，先看水情，还是先查账？",
    },
  },
];

const MODES = [
  { id: "tourism", label: "游历", Icon: MapTrifold },
  { id: "story", label: "入境", Icon: BookOpenText },
];

const FALLBACK_OPENING_LINES = {
  "su-shi-xuzhou": {
    tourism: "你好，我是苏轼。到了徐州，咱们别急着赶景点，先从黄楼边儿走起。我一边陪你看水，一边给你讲讲这座城。你想轻松逛，还是想多听点治水的往事？",
    story: "你来得正好，城外的水势还在涨。别站着了，先跟我到堤上看看。你愿意帮我清点人手，还是先去问问哪一段堤最危险？",
  },
  "chen-xuan-huaian": {
    tourism: "我是陈瑄。咱们从清江浦出发，先看水闸和河道怎么配合，再沿里运河慢慢走。你更想听漕运的故事，还是想要一条好走的路线？",
    story: "你来得正好，闸坝那边有点渗水。咱们先去现场，你帮我看土质和水位，咱们再决定怎么做。",
  },
  "zhang-boxing-suzhou": {
    tourism: "我是张伯行。苏州的河道，得慢慢走、慢慢看。咱们先从巡抚衙门旧址说起，再去看水城里那些和日常生活连在一起的河。你想走得轻松些，还是多听些治河的事？",
    story: "雨下了几日，河堤那边传来消息，物料账目也有些不对。你随我去一趟，先看水情，还是先查账？",
  },
};

function openingLine(character, mode) {
  return (
    character?.opening_lines?.[mode] ||
    FALLBACK_OPENING_LINES[character?.id]?.[mode] ||
    ""
  );
}

function sessionStorageKey(characterId, mode) {
  return `canal-session:${characterId}:${mode}`;
}

function activeModeStorageKey(characterId) {
  return `canal-active-mode:${characterId}`;
}

async function requestJson(url, options) {
  const response = await fetch(url, options);
  const payload = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(payload?.detail || "请求失败，请稍后再试。");
  return payload;
}

function truncate(text, maxLength = 30) {
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text;
}

function typeOut(setMessages, answer) {
  return new Promise((resolve) => {
    if (!answer) {
      resolve();
      return;
    }
    const total = answer.length;
    const perTick = Math.max(1, Math.round(total / 150));
    let shown = 0;
    const timer = setInterval(() => {
      shown = Math.min(total, shown + perTick);
      const text = answer.slice(0, shown);
      setMessages((current) => {
        const next = [...current];
        if (next.length) {
          next[next.length - 1] = { ...next[next.length - 1], content: text };
        }
        return next;
      });
      if (shown >= total) {
        clearInterval(timer);
        resolve();
      }
    }, 20);
  });
}

function useIsDesktop() {
  const [isDesktop, setIsDesktop] = useState(() => window.matchMedia("(min-width: 901px)").matches);
  useEffect(() => {
    const query = window.matchMedia("(min-width: 901px)");
    const handler = (event) => setIsDesktop(event.matches);
    query.addEventListener("change", handler);
    return () => query.removeEventListener("change", handler);
  }, []);
  return isDesktop;
}

function BrandMark() {
  return (
    <svg viewBox="0 0 42 42" aria-hidden="true">
      <path d="M7 25c6-12 15-15 28-8M8 31c9-7 18-7 27-2" />
      <circle className="brand-dot" cx="29" cy="12" r="3" />
    </svg>
  );
}

function Brand({ onClick }) {
  const content = (
    <>
      <span className="brand-mark"><BrandMark /></span>
      <strong>运河人物志</strong>
    </>
  );

  if (onClick) {
    return (
      <button className="brand" type="button" onClick={onClick} aria-label="返回运河人物地图">
        {content}
      </button>
    );
  }

  return <div className="brand">{content}</div>;
}

function Message({ message, characterName, spots = [], spot, onViewSpot, onSpotClick }) {
  const keywords = useMemo(() => {
    const list = [];
    for (const item of spots) list.push(item.name, ...(item.aliases || []));
    return [...new Set(list)].sort((a, b) => b.length - a.length);
  }, [spots]);

  const spotPattern = useMemo(() => {
    if (!keywords.length) return null;
    const escaped = keywords.map((keyword) => keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    return new RegExp(`(${escaped.join("|")})`, "g");
  }, [keywords]);

  function findSpot(word) {
    return spots.find((item) => [item.name, ...(item.aliases || [])].includes(word)) || null;
  }

  function renderText(text, keyPrefix) {
    const parts = spotPattern ? text.split(spotPattern) : [text];
    return parts.map((part, index) => {
      const matched = findSpot(part);
      if (matched) {
        return (
          <button key={`${keyPrefix}-${index}`} type="button" className="spot-mention" onClick={() => onSpotClick?.(matched)}>
            {part}
          </button>
        );
      }
      return <span key={`${keyPrefix}-${index}`}>{part}</span>;
    });
  }

  function renderInline(text, keyPrefix) {
    return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) => (
      part.startsWith("**") && part.endsWith("**")
        ? <strong key={`${keyPrefix}-b-${index}`}>{part.slice(2, -2)}</strong>
        : <span key={`${keyPrefix}-t-${index}`}>{renderText(part, `${keyPrefix}-${index}`)}</span>
    ));
  }

  return (
    <article className={`message ${message.role}`}>
      <span className="message-label">{message.role === "user" ? "你" : characterName}</span>
      <div className="message-body">
        {message.content.split("\n").filter(Boolean).map((line, index) => (
          line.trim().startsWith(">")
            ? <blockquote key={index}>{renderInline(line.trim().replace(/^>\s*/, ""), `l${index}`)}</blockquote>
            : <p key={index}>{renderInline(line, `l${index}`)}</p>
        ))}
      </div>
      {spot && onViewSpot ? (
        <button className="view-spot" type="button" onClick={() => onViewSpot(spot)}>查看实景</button>
      ) : null}
    </article>
  );
}

function CharacterInspector({ character, meta, onEnter }) {
  return (
    <aside className="character-inspector surface" aria-live="polite">
      <img src={meta.portrait} alt={`${character.name}肖像`} />
      <div className="inspector-copy">
        <h2>{character.name}<small>{character.alias}</small></h2>
        <div className="character-meta"><span>{character.dynasty}</span><span>{character.city}</span></div>
        <p className="character-quote">{character.short_intro}</p>
        <div className="place-line">
          <MapPin weight="fill" aria-hidden="true" />
          <span><b>{meta.siteName}</b></span>
        </div>
        <button className="enter-chat" type="button" onClick={() => onEnter(character.id)}>
          与{character.name}同行
          <ArrowRight weight="regular" aria-hidden="true" />
        </button>
      </div>
    </aside>
  );
}

function MapOverview({ characters, selectedId, onSelect, onEnter, loading, error, onRetry }) {
  const character = characters.find((item) => item.id === selectedId) || characters[0];
  const meta = MAP_CHARACTERS[character?.id];

  return (
    <main className="map-page">
      <header className="map-topbar surface">
        <Brand />
        <div className="map-context">
          <span className="map-context-dot" aria-hidden="true" />
          <span>运河人物图</span>
        </div>
      </header>

      <section className="map-canvas">
        <CanalMap characters={characters} selectedId={selectedId} onSelect={onSelect} />

        {loading ? <div className="map-loading" role="status"><i /><span>正在展开水脉</span></div> : null}
        {error ? (
          <div className="map-error" role="alert">
            <span>{error}</span>
            <button type="button" onClick={onRetry}>重试</button>
          </div>
        ) : null}

        {character && meta ? (
          <CharacterInspector character={character} meta={meta} onEnter={onEnter} />
        ) : null}
      </section>
    </main>
  );
}

function ModeSwitcher({ mode, onChange }) {
  return (
    <div className="mode-switch" role="group" aria-label="对话模式">
      {MODES.map(({ id, label, Icon }) => (
        <button key={id} type="button" className={mode === id ? "active" : ""} aria-pressed={mode === id} onClick={() => onChange(id)}>
          <Icon weight="regular" aria-hidden="true" />{label}
        </button>
      ))}
    </div>
  );
}

function ChatComposer({ mode, character, busy, input, onInputChange, onSubmit }) {
  return (
    <form className="composer" onSubmit={onSubmit}>
      <label className="sr-only" htmlFor="message-input">输入消息</label>
      <textarea
        id="message-input"
        rows="1"
        maxLength="4000"
        value={input}
        onChange={onInputChange}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            event.currentTarget.form?.requestSubmit();
          }
        }}
        placeholder={mode === "tourism" ? `问问${character.alias}，该从哪里游起` : `告诉${character.name}，你准备采取什么行动`}
      />
      <button type="submit" disabled={busy || !input.trim()} aria-label="发送消息">
        <ArrowRight weight="regular" aria-hidden="true" />
      </button>
    </form>
  );
}

function ChatView({ character, mode, setMode, onBack }) {
  const currentSessionKey = sessionStorageKey(character.id, mode);
  const [sessionId, setSessionId] = useState(() => sessionStorage.getItem(currentSessionKey));
  const [messages, setMessages] = useState(() => [{ role: "assistant", content: openingLine(character, mode) }]);
  const [suggestions, setSuggestions] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [typing, setTyping] = useState(false);
  const [error, setError] = useState("");
  const [modalSpot, setModalSpot] = useState(null);
  const [dismissedSpotId, setDismissedSpotId] = useState(null);
  const [selectedSpot, setSelectedSpot] = useState(null);
  const [autoSpot, setAutoSpot] = useState(null);
  const messageEndRef = useRef(null);
  const meta = MAP_CHARACTERS[character.id];
  const isDesktop = useIsDesktop();
  const characterSpots = useMemo(() => SPOTS.filter((spot) => spot.characterId === character.id), [character.id]);
  const detectedSpot = useMemo(() => {
    const last = [...messages].reverse().find((message) => message.role === "assistant");
    return detectSpot(last?.content, character.id);
  }, [messages, character.id]);
  const activeSpot = isDesktop
    ? (selectedSpot || (autoSpot && autoSpot.id !== dismissedSpotId ? autoSpot : null))
    : null;

  useEffect(() => {
    if (!typing && detectedSpot) {
      setAutoSpot(detectedSpot);
    }
  }, [detectedSpot, typing]);

  function handleSpotClick(spot) {
    if (!spot) return;
    setSelectedSpot(spot);
    setDismissedSpotId(null);
    if (!isDesktop) setModalSpot(spot);
  }

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function restoreHistory(targetSessionId, targetMode) {
    if (!targetSessionId) return false;
    try {
      const session = await requestJson(`/api/v1/sessions/${targetSessionId}`);
      if (session.character_id !== character.id || session.mode !== targetMode) return false;
      setMessages([{ role: "assistant", content: openingLine(character, targetMode) }, ...session.messages]);
      setSuggestions(session.suggestions || []);
      return true;
    } catch {
      return false;
    }
  }

  useEffect(() => {
    if (!sessionId) return undefined;
    let cancelled = false;
    restoreHistory(sessionId, mode).then((ok) => {
      if (!ok && !cancelled) {
        sessionStorage.removeItem(currentSessionKey);
        setSessionId(null);
      }
    });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function switchMode(nextMode) {
    const openingContent = openingLine(character, nextMode);
    sessionStorage.setItem(activeModeStorageKey(character.id), nextMode);
    setMode(nextMode);
    setBusy(false);
    setError("");
    setSelectedSpot(null);
    setDismissedSpotId(null);
    const nextKey = sessionStorageKey(character.id, nextMode);
    const storedId = sessionStorage.getItem(nextKey);
    setSessionId(storedId);
    if (storedId) {
      setAutoSpot(null);
      restoreHistory(storedId, nextMode);
    } else {
      setMessages([{ role: "assistant", content: openingContent }]);
      setSuggestions([]);
      setAutoSpot(detectSpot(openingContent, character.id));
    }
  }

  function resetConversation() {
    const currentId = sessionId;
    const openingContent = openingLine(character, mode);
    setSessionId(null);
    setMessages([{ role: "assistant", content: openingContent }]);
    setSuggestions([]);
    setError("");
    setBusy(false);
    setSelectedSpot(null);
    setDismissedSpotId(null);
    setAutoSpot(detectSpot(openingContent, character.id));
    sessionStorage.removeItem(currentSessionKey);
    if (currentId) {
      requestJson(`/api/v1/sessions/${currentId}`, { method: "DELETE" }).catch(() => { });
    }
  }

  async function sendMessage(rawMessage) {
    const content = rawMessage.trim();
    if (!content || busy || typing) return;
    setInput("");
    setBusy(true);
    setError("");
    setMessages((current) => [...current, { role: "user", content }]);
    try {
      const result = await requestJson("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ character_id: character.id, mode, message: content, session_id: sessionId }),
      });
      setSessionId(result.session_id);
      sessionStorage.setItem(currentSessionKey, result.session_id);
      setSuggestions(result.suggestions || []);
      setBusy(false);
      setTyping(true);
      setMessages((current) => [...current, { role: "assistant", content: "" }]);
      await typeOut(setMessages, result.answer);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setBusy(false);
      setTyping(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendMessage(input);
  }

  return (
    <>
      <main className={`chat-page ${activeSpot ? "has-spot" : ""}`}>
        {activeSpot ? (
          <SpotPanel
            key={activeSpot.id}
            spot={activeSpot}
            onClose={() => {
              setSelectedSpot(null);
              setDismissedSpotId(activeSpot.id);
            }}
          />
        ) : null}

        <header className="chat-topbar surface">
          <button className="back-map" type="button" onClick={onBack}>
            <ArrowLeft weight="regular" aria-hidden="true" />
            <span>返回地图</span>
          </button>
          <div className="chat-identity">
            <img className="chat-avatar" src={meta.portrait} alt={`${character.name}肖像`} />
            <div className="chat-identity-copy">
              <h1>{character.name}<small>{character.alias}</small></h1>
              <p>{character.dynasty} · {character.city} · {meta.siteName}</p>
            </div>
          </div>
          <div className="chat-actions">
            <ModeSwitcher mode={mode} onChange={switchMode} />
            <button className="new-session" type="button" onClick={() => resetConversation()} aria-label="新建会话">
              <Plus weight="regular" aria-hidden="true" />
            </button>
          </div>
        </header>

        <section className="chat-main">
          <section className="chat-shell surface">
            <div className="messages" aria-live="polite" aria-label="对话记录">
              {messages.map((message, index) => (
                <Message
                  key={`${message.role}-${index}`}
                  message={message}
                  characterName={character.name}
                  spots={characterSpots}
                  spot={message.role === "assistant" ? detectSpot(message.content, character.id) : null}
                  onViewSpot={setModalSpot}
                  onSpotClick={handleSpotClick}
                />
              ))}
              {busy ? (
                <article className="message assistant thinking">
                  <span className="message-label">{character.name}</span>
                  <div className="message-body"><i /><i /><i /></div>
                </article>
              ) : null}
              {error ? <div className="error-note">{error}</div> : null}
              <div ref={messageEndRef} />
            </div>

            <div className="interaction-dock">
              <div className="suggestions" aria-label="推荐问题">
                {suggestions.map((suggestion) => (
                  <button key={suggestion} type="button" title={suggestion} onClick={() => sendMessage(suggestion)}>
                    {truncate(suggestion)}
                  </button>
                ))}
              </div>
              <ChatComposer
                mode={mode}
                character={character}
                busy={busy}
                input={input}
                onInputChange={(event) => setInput(event.target.value)}
                onSubmit={handleSubmit}
              />
            </div>
          </section>
        </section>
      </main>
      {modalSpot ? <SpotModal key={modalSpot.id} spot={modalSpot} onClose={() => setModalSpot(null)} /> : null}
    </>
  );
}

export default function App() {
  const initialChatId = window.location.hash.match(/^#chat\/(.+)$/)?.[1];
  const [characters, setCharacters] = useState(FALLBACK_CHARACTERS);
  const [selectedId, setSelectedId] = useState(initialChatId || "su-shi-xuzhou");
  const [screen, setScreen] = useState(initialChatId ? "chat" : "map");
  const [mode, setMode] = useState(() => (
    initialChatId && sessionStorage.getItem(activeModeStorageKey(initialChatId)) === "story"
      ? "story"
      : "tourism"
  ));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const character = useMemo(() => characters.find((item) => item.id === selectedId) || characters[0], [characters, selectedId]);

  function loadCharacters() {
    setLoading(true);
    setError("");
    requestJson("/api/v1/characters")
      .then((payload) => setCharacters(payload))
      .catch((reason) => setError(`${reason.message}，已显示本地点位。`))
      .finally(() => setLoading(false));
  }

  useEffect(loadCharacters, []);

  useEffect(() => {
    function handleHash() {
      const id = window.location.hash.match(/^#chat\/(.+)$/)?.[1];
      if (id && MAP_CHARACTERS[id]) {
        setSelectedId(id);
        setScreen("chat");
      } else setScreen("map");
    }
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);

  function enterChat(id) {
    setSelectedId(id);
    sessionStorage.setItem(activeModeStorageKey(id), "tourism");
    setMode("tourism");
    window.location.hash = `chat/${id}`;
    setScreen("chat");
  }

  function returnToMap() {
    history.pushState(null, "", window.location.pathname + window.location.search);
    setScreen("map");
  }

  return (
    <div className="page-canvas">
      <div className="page-paper" aria-hidden="true" />
      {screen === "chat" && character ? (
        <ChatView key={character.id} character={character} mode={mode} setMode={setMode} onBack={returnToMap} />
      ) : (
        <MapOverview characters={characters} selectedId={selectedId} onSelect={setSelectedId} onEnter={enterChat} loading={loading} error={error} onRetry={loadCharacters} />
      )}
    </div>
  );
}
