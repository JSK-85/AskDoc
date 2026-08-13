export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="glass flex items-center gap-1.5 rounded-2xl rounded-bl-md px-4 py-3.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="dot-bounce h-1.5 w-1.5 rounded-full bg-foreground/70"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
}
