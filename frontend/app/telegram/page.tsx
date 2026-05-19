import { AppSidebar } from "@/components/AppSidebar";
import { TelegramConnectPanel } from "@/components/TelegramConnectPanel";

export default function TelegramPage() {
  return (
    <main className="app-shell">
      <AppSidebar active="telegram" />
      <section className="dashboard">
        <TelegramConnectPanel />
      </section>
    </main>
  );
}
