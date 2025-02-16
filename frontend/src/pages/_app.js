import NavBar, { NavBarProvider } from "@/components/NavBar/NavBar";
import "@/styles/globals.css";

export default function App({ Component, pageProps }) {

    return (
        <NavBarProvider>
            <div style={{'display': 'flex', 'justifyContent': 'center', 'margin': 'var(--margin-top) var(--margin)', 'marginBottom': '30vh'}}>
                <div style={{'width': 'calc(min(800px, 100%))'}}>
                    <div style={{ 'marginBottom': 'var(--margin-top)', 'padding': '5px 0px', 'position': 'sticky', 'top': '0px', 'background': 'var(--background)'}}>
                        <NavBar />
                    </div>
                    <Component {...pageProps} />
                </div>
            </div>
        </NavBarProvider>
    );
}
