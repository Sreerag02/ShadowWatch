import { Component } from 'react'
export default class ErrorBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    if (this.state.failed) return <div className="state error" role="alert"><h1>Workspace could not be displayed</h1><p>An unexpected response or application error occurred. Reload the workspace to retry.</p><button className="button" onClick={() => window.location.reload()}>Reload workspace</button></div>
    return this.props.children
  }
}
